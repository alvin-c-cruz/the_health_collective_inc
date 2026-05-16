from flask import Blueprint, render_template, request, redirect, url_for, flash

from application.extensions import db
from application.blueprints.user import login_required, roles_accepted

from . import app_name, app_label
from .models import TransactionType as Obj

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route('/', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    types = Obj.query.order_by(Obj.sort_order).all()
    return render_template('transaction_type/home.html', types=types, app_label=app_label)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add():
    errors = {}
    obj = Obj()
    obj.active = True

    if request.method == 'POST':
        obj.type_code = request.form.get('type_code', '').strip().lower().replace(' ', '_')
        obj.type_name = request.form.get('type_name', '').strip()
        obj.description = request.form.get('description', '').strip()
        obj.icon = request.form.get('icon', 'bi-tag').strip()
        obj.icon_color = request.form.get('icon_color', 'ic-blue').strip()
        obj.badge_color = request.form.get('badge_color', 'thc-badge-blue').strip()
        obj.report_category = request.form.get('report_category', 'walk_in').strip()
        obj.sort_order = int(request.form.get('sort_order') or 99)
        obj.active = 'active' in request.form

        if not obj.type_code:
            errors['type_code'] = 'Type code is required.'
        elif Obj.query.filter_by(type_code=obj.type_code).first():
            errors['type_code'] = 'This type code already exists.'
        if not obj.type_name:
            errors['type_name'] = 'Type name is required.'

        if not errors:
            db.session.add(obj)
            db.session.commit()
            flash(f'Transaction type "{obj.type_name}" added.', 'success')
            return redirect(url_for('transaction_type.home'))

    return render_template('transaction_type/form.html',
                           obj=obj, errors=errors, is_new=True, app_label=app_label)


@bp.route('/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit(record_id):
    obj = Obj.query.get_or_404(record_id)
    errors = {}

    if request.method == 'POST':
        new_code = request.form.get('type_code', '').strip().lower().replace(' ', '_')
        obj.type_name = request.form.get('type_name', '').strip()
        obj.description = request.form.get('description', '').strip()
        obj.icon = request.form.get('icon', 'bi-tag').strip()
        obj.icon_color = request.form.get('icon_color', 'ic-blue').strip()
        obj.badge_color = request.form.get('badge_color', 'thc-badge-blue').strip()
        obj.report_category = request.form.get('report_category', 'walk_in').strip()
        obj.sort_order = int(request.form.get('sort_order') or 99)
        obj.active = 'active' in request.form

        if not new_code:
            errors['type_code'] = 'Type code is required.'
        elif new_code != obj.type_code:
            if Obj.query.filter_by(type_code=new_code).first():
                errors['type_code'] = 'This type code already exists.'
            else:
                obj.type_code = new_code

        if not obj.type_name:
            errors['type_name'] = 'Type name is required.'

        if not errors:
            db.session.commit()
            flash(f'Transaction type "{obj.type_name}" updated.', 'success')
            return redirect(url_for('transaction_type.home'))

    return render_template('transaction_type/form.html',
                           obj=obj, errors=errors, is_new=False, app_label=app_label)


@bp.route('/toggle/<int:record_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def toggle(record_id):
    obj = Obj.query.get_or_404(record_id)
    obj.active = not obj.active
    db.session.commit()
    status = 'enabled' if obj.active else 'disabled'
    flash(f'"{obj.type_name}" {status}.', 'success' if obj.active else 'warning')
    return redirect(url_for('transaction_type.home'))
