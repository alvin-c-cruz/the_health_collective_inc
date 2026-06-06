from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user

# Centralized audit logging
from application.blueprints.audit.utils import (
    log_create,
    log_delete,
    log_update,
    model_to_dict,
)
from application.blueprints.user import login_required, roles_accepted
from application.extensions import db, ph_today

from ...register.company.models import Company
from ..daily_sales.models import Transaction
from . import app_label, app_name
from .models import ApeBatch

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = [app_label, "Daily Sales"]


@bp.route("/")
@login_required
@roles_accepted(ROLES_ACCEPTED)
def home():
    batches = ApeBatch.query.order_by(ApeBatch.batch_date.desc()).all()
    return render_template(f"{app_name}/home.html", batches=batches)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_accepted(ROLES_ACCEPTED)
def new_batch():
    companies = (
        Company.query.filter_by(active=True).order_by(Company.company_name).all()
    )

    if request.method == "POST":
        f = request.form
        company_id = f.get("company_id", type=int)
        batch_date = f.get("batch_date") or str(ph_today())
        loa_soa_number = (f.get("loa_soa_number") or "").strip()
        reference_number = (f.get("reference_number") or "").strip()
        try:
            package_amount = float(f.get("package_amount") or 0)
        except ValueError:
            package_amount = 0
        notes = (f.get("notes") or "").strip()

        if not company_id:
            flash("Please select a company.", "danger")
        else:
            batch = ApeBatch(
                company_id=company_id,
                batch_date=batch_date,
                loa_soa_number=loa_soa_number,
                reference_number=reference_number,
                package_amount=package_amount,
                notes=notes,
                created_by=current_user.id,
                created_at=str(ph_today()),
            )
            db.session.add(batch)
            db.session.flush()

            # Log APE batch creation
            try:
                log_create(
                    module="ape_batch",
                    record_id=batch.id,
                    record_identifier=str(batch),
                    new_values=model_to_dict(
                        batch,
                        [
                            "company_id",
                            "batch_date",
                            "loa_soa_number",
                            "reference_number",
                            "package_amount",
                            "notes",
                            "created_by",
                            "created_at",
                        ],
                    ),
                    notes="APE batch created",
                )
            except Exception as e:
                # Don't break the operation if audit logging fails
                print(f"Audit logging failed: {e}")

            db.session.commit()
            flash("APE Batch created.", "success")
            return redirect(url_for(f"{app_name}.view_batch", batch_id=batch.id))

    return render_template(
        f"{app_name}/form.html", companies=companies, today=str(ph_today())
    )


@bp.route("/<int:batch_id>")
@login_required
@roles_accepted(ROLES_ACCEPTED)
def view_batch(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    transactions = Transaction.query.filter_by(ape_batch_id=batch_id).all()
    return render_template(
        f"{app_name}/view.html", batch=batch, transactions=transactions
    )


@bp.route("/<int:batch_id>/edit", methods=["GET", "POST"])
@login_required
@roles_accepted(ROLES_ACCEPTED)
def edit_batch(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    companies = (
        Company.query.filter_by(active=True).order_by(Company.company_name).all()
    )

    if request.method == "POST":
        # Capture old values before update
        old_values = model_to_dict(
            batch,
            [
                "company_id",
                "batch_date",
                "loa_soa_number",
                "reference_number",
                "package_amount",
                "notes",
            ],
        )

        f = request.form
        batch.company_id = f.get("company_id", type=int)
        batch.batch_date = f.get("batch_date") or batch.batch_date
        batch.loa_soa_number = (f.get("loa_soa_number") or "").strip()
        batch.reference_number = (f.get("reference_number") or "").strip()
        try:
            batch.package_amount = float(f.get("package_amount") or 0)
        except ValueError:
            pass
        batch.notes = (f.get("notes") or "").strip()

        # Capture new values after update
        new_values = model_to_dict(
            batch,
            [
                "company_id",
                "batch_date",
                "loa_soa_number",
                "reference_number",
                "package_amount",
                "notes",
            ],
        )

        # Log APE batch update
        try:
            log_update(
                module="ape_batch",
                record_id=batch.id,
                record_identifier=str(batch),
                old_values=old_values,
                new_values=new_values,
                notes="APE batch updated",
            )
        except Exception as e:
            # Don't break the operation if audit logging fails
            print(f"Audit logging failed: {e}")

        db.session.commit()
        flash("APE Batch updated.", "success")
        return redirect(url_for(f"{app_name}.view_batch", batch_id=batch.id))

    return render_template(
        f"{app_name}/form.html",
        batch=batch,
        companies=companies,
        today=batch.batch_date,
    )


@bp.route("/<int:batch_id>/delete", methods=["POST"])
@login_required
@roles_accepted(ROLES_ACCEPTED)
def delete_batch(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    if batch.transactions:
        flash("Cannot delete batch — it has linked transactions.", "danger")
        return redirect(url_for(f"{app_name}.view_batch", batch_id=batch_id))

    # Capture values before delete
    old_values = model_to_dict(
        batch,
        [
            "company_id",
            "batch_date",
            "loa_soa_number",
            "package_amount",
            "notes",
            "created_by",
            "created_at",
        ],
    )
    batch_identifier = str(batch)

    db.session.delete(batch)

    # Log APE batch deletion
    try:
        log_delete(
            module="ape_batch",
            record_id=batch_id,
            record_identifier=batch_identifier,
            old_values=old_values,
            notes="APE batch deleted",
        )
    except Exception as e:
        # Don't break the operation if audit logging fails
        print(f"Audit logging failed: {e}")

    db.session.commit()
    flash("APE Batch deleted.", "warning")
    return redirect(url_for(f"{app_name}.home"))


@bp.route("/<int:batch_id>/soa")
@login_required
@roles_accepted(ROLES_ACCEPTED)
def soa(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    transactions = (
        Transaction.query.filter_by(ape_batch_id=batch_id)
        .order_by(Transaction.record_date)
        .all()
    )
    return render_template(
        f"{app_name}/soa.html", batch=batch, transactions=transactions
    )


@bp.route("/guide")
@login_required
@roles_accepted(ROLES_ACCEPTED)
def guide():
    return render_template(f"{app_name}/guide.html")


# AJAX — return batch details (package_amount) for the daily_sales form
@bp.route("/api/<int:batch_id>")
@login_required
def batch_info(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    return jsonify(
        {
            "id": batch.id,
            "company": batch.company.company_name,
            "batch_date": batch.batch_date,
            "loa_soa_number": batch.loa_soa_number,
            "package_amount": batch.package_amount,
        }
    )
