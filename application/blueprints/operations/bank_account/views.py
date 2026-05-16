from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError

from application.blueprints.user import login_required, roles_accepted
from application.extensions import db

from . import app_name, app_label
from .models import BankAccount as Obj
from .forms import Form

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    rows = Obj.query.order_by(Obj.bank_name).all()
    return render_template(f"{app_name}/home.html", rows=rows, app_label=app_label)


@bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add():
    form = Form()
    if request.method == "POST":
        form._post(request.form)
        if form._validate_on_submit():
            form._save()
            flash("Bank account added.", "success")
            return redirect(url_for(f"{app_name}.home"))
    return render_template(f"{app_name}/form.html", form=form, app_label=app_label)


@bp.route("/edit/<int:record_id>", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit(record_id):
    obj = Obj.query.get_or_404(record_id)
    form = Form()
    if request.method == "POST":
        form._post(request.form)
        if form._validate_on_submit():
            form._save()
            flash("Bank account updated.", "success")
            return redirect(url_for(f"{app_name}.home"))
    else:
        form._populate(obj)
    return render_template(f"{app_name}/form.html", form=form, app_label=app_label)


@bp.route("/delete/<int:record_id>", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete(record_id):
    obj = Obj.query.get_or_404(record_id)
    try:
        db.session.delete(obj)
        db.session.commit()
        flash(f"{obj} deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Cannot delete — this bank account is referenced by existing collections.", "danger")
    return redirect(url_for(f"{app_name}.home"))
