from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from sqlalchemy.exc import IntegrityError

from application.extensions import db
from application.blueprints.user import login_required, roles_accepted
from .models import Company as Obj
from .models import ObjAdmin as Approver
from .models import ObjUser as Preparer
from .forms import Form
from . import app_name, app_label

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
    if request.method == "POST":
        form = Form()
        form._post(request.form, current_user.id)
        if form._validate_on_submit():
            form._save()
            return redirect(url_for(f"{app_name}.home"))
    else:
        form = Form()
    return render_template(f"{app_name}/form.html", form=form)


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
    try:
        preparer = obj.preparer
        if preparer:
            db.session.delete(preparer)
        db.session.delete(obj)
        db.session.commit()
        flash(f"{obj} deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash(f"Cannot delete {obj} — it has related records.", "danger")
    return redirect(url_for(f"{app_name}.home"))


@bp.route("/quick_add", methods=["POST"])
@login_required
def quick_add():
    company_name = (request.json or {}).get("company_name", "").strip()
    if not company_name:
        return jsonify({"error": "Company name is required."}), 400
    company = Obj(company_name=company_name, active=True)
    db.session.add(company)
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
