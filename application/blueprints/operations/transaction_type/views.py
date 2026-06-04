from flask import Blueprint, render_template, request, redirect, url_for, flash, abort

from application.extensions import db
from application.blueprints.user import login_required, roles_accepted, current_user

from . import app_name, app_label
from .models import TransactionType as Obj
from application.blueprints.register.tender.models import Tender
from application.blueprints.audit.utils import log_create, log_update, log_delete, log_status_change, model_to_dict

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


@bp.route('/', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    from application.blueprints.operations.daily_sales.models import Transaction
    from sqlalchemy import func
    types = Obj.query.order_by(Obj.sort_order).all()
    counts = dict(
        db.session.query(Transaction.transaction_type_id, func.count(Transaction.id))
        .group_by(Transaction.transaction_type_id).all()
    )
    return render_template('transaction_type/home.html', types=types,
                           app_label=app_label, txn_counts=counts)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add():
    errors = {}
    obj = Obj()
    obj.active = True

    # Get all tenders for the checkbox list
    tenders = Tender.query.order_by(Tender.sort_order.desc()).all()

    if request.method == 'POST':
        obj.type_code = request.form.get('type_code', '').strip().lower().replace(' ', '_')
        obj.type_name = request.form.get('type_name', '').strip()
        obj.description = request.form.get('description', '').strip()
        obj.icon = request.form.get('icon', 'bi-tag').strip()
        obj.icon_color = request.form.get('icon_color', 'ic-blue').strip()
        obj.badge_color = request.form.get('badge_color', 'thc-badge-blue').strip()
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

            # Update tender transaction_types based on checkboxes
            selected_tender_ids = request.form.getlist('tenders')
            for tender in tenders:
                existing_types = (tender.transaction_types or '').split(',')
                existing_types = [t for t in existing_types if t]  # Remove empty strings

                if str(tender.id) in selected_tender_ids:
                    # Add this type if not already present
                    if obj.type_code not in existing_types:
                        existing_types.append(obj.type_code)
                else:
                    # Remove this type if present
                    if obj.type_code in existing_types:
                        existing_types.remove(obj.type_code)

                tender.transaction_types = ','.join(existing_types) if existing_types else None

            # Log creation
            try:
                log_create(
                    module='transaction_type',
                    record_id=obj.id,
                    record_identifier=f"{obj.type_name} ({obj.type_code})",
                    new_values=model_to_dict(obj, ['type_code', 'type_name', 'description', 'icon', 'icon_color', 'badge_color', 'sort_order', 'active']),
                    notes='Transaction type created'
                )
            except Exception as e:
                flash(f'Transaction type saved, but audit logging failed: {str(e)}', 'warning')
                print(f"Audit logging failed: {e}")

            db.session.commit()
            flash(f'Service type "{obj.type_name}" added.', 'success')
            return redirect(url_for('transaction_type.home'))

    return render_template('transaction_type/form.html',
                           obj=obj, errors=errors, is_new=True, app_label=app_label, tenders=tenders)


@bp.route('/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit(record_id):
    obj = Obj.query.get_or_404(record_id)
    errors = {}

    # Get all tenders for the checkbox list
    tenders = Tender.query.order_by(Tender.sort_order.desc()).all()

    if request.method == 'POST':
        # Capture old values before updating
        old_values = model_to_dict(obj, ['type_code', 'type_name', 'description', 'icon', 'icon_color', 'badge_color', 'sort_order', 'active'])

        old_code = obj.type_code
        new_code = request.form.get('type_code', '').strip().lower().replace(' ', '_')
        obj.type_name = request.form.get('type_name', '').strip()
        obj.description = request.form.get('description', '').strip()
        obj.icon = request.form.get('icon', 'bi-tag').strip()
        obj.icon_color = request.form.get('icon_color', 'ic-blue').strip()
        obj.badge_color = request.form.get('badge_color', 'thc-badge-blue').strip()
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
            # Update tender transaction_types based on checkboxes
            selected_tender_ids = request.form.getlist('tenders')
            for tender in tenders:
                existing_types = (tender.transaction_types or '').split(',')
                existing_types = [t for t in existing_types if t]  # Remove empty strings

                # If type_code changed, update old references
                if old_code != new_code and old_code in existing_types:
                    existing_types.remove(old_code)

                if str(tender.id) in selected_tender_ids:
                    # Add this type if not already present
                    if new_code not in existing_types:
                        existing_types.append(new_code)
                else:
                    # Remove this type if present
                    if new_code in existing_types:
                        existing_types.remove(new_code)

                tender.transaction_types = ','.join(existing_types) if existing_types else None

            # Log update
            try:
                new_values = model_to_dict(obj, ['type_code', 'type_name', 'description', 'icon', 'icon_color', 'badge_color', 'sort_order', 'active'])
                log_update(
                    module='transaction_type',
                    record_id=obj.id,
                    record_identifier=f"{obj.type_name} ({obj.type_code})",
                    old_values=old_values,
                    new_values=new_values,
                    notes='Transaction type updated'
                )
            except Exception as e:
                flash(f'Transaction type updated, but audit logging failed: {str(e)}', 'warning')
                print(f"Audit logging failed: {e}")

            db.session.commit()
            flash(f'Service type "{obj.type_name}" updated.', 'success')
            return redirect(url_for('transaction_type.home'))

    return render_template('transaction_type/form.html',
                           obj=obj, errors=errors, is_new=False, app_label=app_label, tenders=tenders)


@bp.route('/toggle/<int:record_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def toggle(record_id):
    obj = Obj.query.get_or_404(record_id)
    old_status = 'active' if obj.active else 'inactive'
    obj.active = not obj.active
    new_status = 'active' if obj.active else 'inactive'

    # Log status change
    try:
        log_status_change(
            module='transaction_type',
            record_id=obj.id,
            record_identifier=f"{obj.type_name} ({obj.type_code})",
            action='toggled',
            old_status=old_status,
            new_status=new_status,
            notes=f'Transaction type {"enabled" if obj.active else "disabled"}'
        )
    except Exception as e:
        flash(f'Status changed, but audit logging failed: {str(e)}', 'warning')
        print(f"Audit logging failed: {e}")

    db.session.commit()
    status = 'enabled' if obj.active else 'disabled'
    flash(f'"{obj.type_name}" {status}.', 'success' if obj.active else 'warning')
    return redirect(url_for('transaction_type.home'))


@bp.route('/reorder', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def reorder():
    from flask import jsonify
    ids = request.json.get('ids', [])
    for i, record_id in enumerate(ids):
        obj = Obj.query.get(record_id)
        if obj:
            obj.sort_order = (i + 1) * 10
    db.session.commit()
    return jsonify(ok=True)


@bp.route('/delete/<int:record_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete(record_id):
    if not current_user.superuser:
        abort(403)
    from application.blueprints.operations.daily_sales.models import Transaction
    obj = Obj.query.get_or_404(record_id)
    count = Transaction.query.filter_by(transaction_type_id=record_id).count()
    if count > 0:
        flash(f'Cannot delete "{obj.type_name}" — it has {count} linked transaction(s).', 'danger')
        return redirect(url_for('transaction_type.home'))

    # Capture old values before deletion
    old_values = model_to_dict(obj, ['type_code', 'type_name', 'description', 'icon', 'icon_color', 'badge_color', 'sort_order', 'active'])
    record_identifier = f"{obj.type_name} ({obj.type_code})"

    db.session.delete(obj)

    # Log deletion
    try:
        log_delete(
            module='transaction_type',
            record_id=record_id,
            record_identifier=record_identifier,
            old_values=old_values,
            reason='Transaction type deleted by superuser'
        )
    except Exception as e:
        flash(f'Transaction type deleted, but audit logging failed: {str(e)}', 'warning')
        print(f"Audit logging failed: {e}")

    db.session.commit()
    flash(f'Service type "{obj.type_name}" deleted.', 'success')
    return redirect(url_for('transaction_type.home'))
