from flask import Blueprint, render_template, render_template_string, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError

from application.blueprints.user import login_required, roles_accepted
from application.extensions import db

from . import app_name, app_label
from application.blueprints.operations.daily_sales.models import Payee as Obj
from .forms import Form
from application.blueprints.audit.utils import log_delete, model_to_dict

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route("/")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    rows = Obj.query.order_by(Obj.name).all()
    return render_template(f"{app_name}/home.html", rows=rows, app_label=app_label)


@bp.route("/add", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add():
    if request.method == "POST":
        form = Form()
        form._post(request.form)
        if form._validate_on_submit():
            form._save()
            flash("Payee added.", "success")
            return redirect(url_for(f"{app_name}.home"))
    else:
        form = Form()

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
            flash("Payee updated.", "success")
            return redirect(url_for(f"{app_name}.home"))
    else:
        form._populate(obj)
    return render_template(f"{app_name}/form.html", form=form, app_label=app_label)


@bp.route("/add-popup", methods=["GET", "POST"])
@login_required
def add_popup():
    """Add payee in popup window - no navbar, modal-style form"""
    if request.method == "POST":
        form = Form()
        form._post(request.form)
        if form._validate_on_submit():
            obj = form._save()
            # Send postMessage to parent window with payee details
            return render_template_string(
                '<!doctype html><html><head><meta charset="utf-8"></head><body>'
                '<script>'
                'if(window.opener){'
                'window.opener.postMessage({type:"payee_added",payee_id:{{ id | tojson }},payee_name:{{ name | tojson }}},"*");'
                '}'
                'window.close();'
                '</script>'
                '<p style="font-family:sans-serif;padding:2rem;">Payee saved. This window will close automatically.</p>'
                '</body></html>',
                id=obj.id,
                name=obj.name
            )
    else:
        form = Form()

    return render_template(f"{app_name}/form_popup.html", form=form)


@bp.route("/delete/<int:record_id>", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete(record_id):
    obj = Obj.query.get_or_404(record_id)

    # Capture old values before deletion
    old_values = model_to_dict(obj, ['name', 'description', 'active'])
    record_identifier = f"{obj.name}"

    try:
        db.session.delete(obj)

        # Log deletion
        log_delete(
            module='payee',
            record_id=record_id,
            record_identifier=record_identifier,
            old_values=old_values,
            reason='Payee deleted by user'
        )

        db.session.commit()
        flash(f"{record_identifier} deleted.", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Cannot delete — this payee is referenced by existing records.", "danger")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting payee: {str(e)}", "danger")
        print(f"Delete operation failed: {e}")
    return redirect(url_for(f"{app_name}.home"))
