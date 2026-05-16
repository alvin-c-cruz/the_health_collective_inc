from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user

from application.extensions import db
from application.blueprints.user import login_required, roles_accepted
from .models import ApeBatch
from ..daily_sales.models import Transaction
from ...register.company.models import Company

from . import app_name, app_label

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    batches = ApeBatch.query.order_by(ApeBatch.batch_date.desc()).all()
    return render_template(f"{app_name}/home.html", batches=batches)


@bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_batch():
    companies = Company.query.filter_by(active=True).order_by(Company.company_name).all()

    if request.method == "POST":
        f = request.form
        company_id = f.get("company_id", type=int)
        batch_date = f.get("batch_date") or str(date.today())
        loa_soa_number = (f.get("loa_soa_number") or "").strip()
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
                package_amount=package_amount,
                notes=notes,
                created_by=current_user.id,
                created_at=str(date.today()),
            )
            db.session.add(batch)
            db.session.commit()
            flash("APE Batch created.", "success")
            return redirect(url_for(f"{app_name}.view_batch", batch_id=batch.id))

    return render_template(f"{app_name}/form.html", companies=companies, today=str(date.today()))


@bp.route("/<int:batch_id>")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def view_batch(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    transactions = Transaction.query.filter_by(ape_batch_id=batch_id).all()
    return render_template(f"{app_name}/view.html", batch=batch, transactions=transactions)


@bp.route("/<int:batch_id>/edit", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit_batch(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    companies = Company.query.filter_by(active=True).order_by(Company.company_name).all()

    if request.method == "POST":
        f = request.form
        batch.company_id = f.get("company_id", type=int)
        batch.batch_date = f.get("batch_date") or batch.batch_date
        batch.loa_soa_number = (f.get("loa_soa_number") or "").strip()
        try:
            batch.package_amount = float(f.get("package_amount") or 0)
        except ValueError:
            pass
        batch.notes = (f.get("notes") or "").strip()
        db.session.commit()
        flash("APE Batch updated.", "success")
        return redirect(url_for(f"{app_name}.view_batch", batch_id=batch.id))

    return render_template(f"{app_name}/form.html", batch=batch, companies=companies, today=batch.batch_date)


@bp.route("/<int:batch_id>/delete", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete_batch(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    if batch.transactions:
        flash("Cannot delete batch — it has linked transactions.", "danger")
        return redirect(url_for(f"{app_name}.view_batch", batch_id=batch_id))
    db.session.delete(batch)
    db.session.commit()
    flash("APE Batch deleted.", "warning")
    return redirect(url_for(f"{app_name}.home"))


@bp.route("/guide")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def guide():
    return render_template(f"{app_name}/guide.html")


# AJAX — return batch details (package_amount) for the daily_sales form
@bp.route("/api/<int:batch_id>")
@login_required
def batch_info(batch_id):
    batch = ApeBatch.query.get_or_404(batch_id)
    return jsonify({
        "id": batch.id,
        "company": batch.company.company_name,
        "batch_date": batch.batch_date,
        "loa_soa_number": batch.loa_soa_number,
        "package_amount": batch.package_amount,
    })
