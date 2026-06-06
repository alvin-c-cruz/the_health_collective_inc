from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    url_for,
)
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from application.blueprints.audit.utils import (
    log_create,
    log_delete,
    model_to_dict,
)
from application.blueprints.user import login_required, roles_accepted
from application.extensions import db

from . import app_label, app_name
from .forms import Form
from .models import Company as Obj
from .models import ObjAdmin as Approver

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    rows = Obj.query.order_by(Obj.company_name).all()
    return render_template(f"{app_name}/home.html", rows=rows)


@bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add():
    popup = request.args.get("popup") == "1"
    if request.method == "POST":
        form = Form()
        form._post(request.form, current_user.id)
        if form._validate_on_submit():
            form._save()
            if popup:
                company = Obj.query.get(form.id)
                return render_template_string(
                    '<!doctype html><html><head><meta charset="utf-8"></head><body>'
                    "<script>"
                    "if(window.opener){"
                    'window.opener.postMessage({type:"company_added",id:{{ id }},company_name:{{ name | tojson }}},"*");'
                    "}"
                    "window.close();"
                    "</script>"
                    "</body></html>",
                    id=company.id,
                    name=company.company_name,
                )
            return redirect(url_for(f"{app_name}.home"))
    else:
        form = Form()
    return render_template(f"{app_name}/form.html", form=form, popup=popup)


@bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit(record_id):
    if request.method == "POST":
        form = Form()
        form._post(request.form, current_user.id)
        if form._validate_on_submit():
            form._save()
            return redirect(url_for(f"{app_name}.home"))
    else:
        obj = Obj.query.get_or_404(record_id)
        form = Form()
        form._populate(obj)
    return render_template(f"{app_name}/form.html", form=form)


@bp.route("/delete/<int:record_id>", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete(record_id):
    obj = Obj.query.get_or_404(record_id)

    # Capture values before deletion
    old_values = model_to_dict(
        obj,
        [
            "company_name",
            "contact_person",
            "contact_number",
            "address",
            "tin",
            "active",
        ],
    )
    record_id_for_log = obj.id
    identifier = str(obj)

    try:
        preparer = obj.preparer
        if preparer:
            db.session.delete(preparer)
        db.session.delete(obj)

        # Log deletion before commit
        log_delete(
            module="company",
            record_id=record_id_for_log,
            record_identifier=identifier,
            old_values=old_values,
        )

        db.session.commit()
        flash(f"{identifier} deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash(f"Cannot delete {obj} — it has related records.", "danger")
    return redirect(url_for(f"{app_name}.home"))


@bp.route("/quick_add", methods=["POST"])
@login_required
def quick_add():
    data = request.json or {}
    company_name = data.get("company_name", "").strip()
    if not company_name:
        return jsonify({"error": "Company name is required."}), 400
    company = Obj(
        company_name=company_name,
        contact_person=data.get("contact_person", "").strip() or None,
        contact_number=data.get("contact_number", "").strip() or None,
        address=data.get("address", "").strip() or None,
        tin=data.get("tin", "").strip() or None,
        active=True,
    )
    db.session.add(company)
    db.session.flush()

    # Log creation after flush to get ID
    log_create(
        module="company",
        record_id=company.id,
        record_identifier=str(company),
        new_values=model_to_dict(
            company,
            [
                "company_name",
                "contact_person",
                "contact_number",
                "address",
                "tin",
                "active",
            ],
        ),
        notes="Company quick-added",
    )

    db.session.commit()
    return jsonify({"id": company.id, "company_name": company.company_name})


@bp.route("/approve/<int:record_id>")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def approve(record_id):
    if not current_user.admin:
        flash("Administrator rights required.", "danger")
        return redirect(url_for(f"{app_name}.home"))
    obj = Obj.query.get_or_404(record_id)
    db.session.add(Approver(company_id=record_id, user_id=current_user.id))
    db.session.commit()
    flash(f"Approved: {obj.company_name}", "success")
    return redirect(url_for(f"{app_name}.home"))


@bp.route("/unlock/<int:record_id>")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def unlock(record_id):
    if not current_user.admin:
        flash("Administrator rights required.", "danger")
        return redirect(url_for(f"{app_name}.home"))
    obj = Obj.query.get_or_404(record_id)
    approver = Approver.query.filter_by(company_id=record_id).first()
    if approver:
        db.session.delete(approver)
        db.session.commit()
    flash(f"Unlocked: {obj.company_name}", "warning")
    return redirect(url_for(f"{app_name}.home"))
