from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import date
from sqlalchemy import func

from ...user import login_required, roles_accepted, current_user
from ...register.customer import Customer
from application.extensions import ph_today

from . import app_label, app_name
from .models import Transaction, TransactionDetail, TransactionTender, TransactionType
from .forms import Form
from ...register.product_type import ProductType
from ...register.tender import Tender
from ...register.sex.models import Sex

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


def _can_transact():
    """True for SuperAdmin, Admin, and Staff — the levels that may create/edit transactions."""
    return bool(current_user.superuser or current_user.admin or current_user.staff)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generate_record_number():
    from .models import Transaction
    last = Transaction.query.filter(
        Transaction.record_number.isnot(None)
    ).order_by(Transaction.record_number.desc()).first()
    if last and last.record_number:
        try:
            seq = int(last.record_number) + 1
        except ValueError:
            seq = 1
    else:
        seq = 1
    return f"{seq:05d}"


# ---------------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------------

@bp.route("/", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    from datetime import timedelta

    today = ph_today()
    date_str = request.args.get('date', str(today))
    try:
        selected_date = date.fromisoformat(date_str)
    except ValueError:
        selected_date = today

    transactions = Transaction.query.filter(
        Transaction.record_date == str(selected_date)
    ).order_by(Transaction.id.desc()).all()

    total_sales = sum(
        sum(d.amount - d.discount for d in t.transaction_details) - (t.discount or 0)
        for t in transactions
        if t.submitted and not t.cancelled
    )

    cash_on_hand = sum(
        sum(td.amount for td in t.transaction_tenders
            if td.tender and 'cash' in td.tender.tender_name.lower())
        for t in transactions
        if t.submitted and not t.cancelled
    )

    class Summary:
        pass

    summary = Summary()
    summary.total_sales = total_sales
    summary.cash_on_hand = cash_on_hand
    summary.transaction_count = len([t for t in transactions if t.submitted and not t.cancelled])

    all_tenders = Tender.query.order_by(Tender.tender_name).all()
    txn_type_tenders = {}
    for t in all_tenders:
        if t.transaction_types:
            for tt in t.transaction_types.split(','):
                tt = tt.strip()
                if tt:
                    txn_type_tenders.setdefault(tt, []).append(t)

    transaction_types = TransactionType.query.filter_by(active=True).order_by(TransactionType.sort_order).all()

    # Build a lookup dict: type_code -> TransactionType for template use
    type_lookup = {tt.type_code: tt for tt in transaction_types}

    context = {
        "app_label": app_label,
        "today": today,
        "selected_date": selected_date,
        "is_today": selected_date == today,
        "prev_date": selected_date - timedelta(days=1),
        "next_date": selected_date + timedelta(days=1),
        "summary": summary,
        "transactions": transactions,
        "txn_type_tenders": txn_type_tenders,
        "transaction_types": transaction_types,
        "type_lookup": type_lookup,
    }
    return render_template("daily_sales/home.html", **context)


# ---------------------------------------------------------------------------
# New transaction  (GET: show form | POST: save)
# ---------------------------------------------------------------------------

@bp.route('/transaction/new', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_transaction():
    if not _can_transact():
        abort(403)

    ape_batch_id_arg = request.args.get('ape_batch_id', type=int)
    locked_from_batch = False

    if ape_batch_id_arg:
        ape_type = TransactionType.query.filter_by(type_code='ape').first()
        transaction_type = ape_type
        locked_from_batch = True
    else:
        type_id = request.args.get('type_id', type=int)
        transaction_type = TransactionType.query.get(type_id) if type_id else TransactionType.query.order_by(TransactionType.sort_order).first()

    form = Form()
    form.user_prepare_id = current_user.id
    form.record_date = str(ph_today())
    form.record_number = _generate_record_number()
    form.transaction_type_id = transaction_type.id if transaction_type else None
    if ape_batch_id_arg:
        form.ape_batch_id = ape_batch_id_arg

    prefill_tender_id = request.args.get('prefill_tender_id', type=int)
    if prefill_tender_id:
        form.tenders[0][1].tender_id = prefill_tender_id

    if request.method == 'POST':
        form._post(request.form)
        transaction_type = TransactionType.query.get(form.transaction_type_id) if form.transaction_type_id else None
        if not form.record_number:
            form.record_number = _generate_record_number()

        action = request.form.get('action', 'save')

        if form._validate_on_submit():
            form._save()

            if action == 'submit':
                form._submit()
                flash('Transaction saved and submitted.', 'success')
            else:
                flash('Transaction saved as draft.', 'success')

            return redirect(url_for(f'{app_name}.edit_transaction', transaction_id=form.id))

    product_types = ProductType.query.order_by(ProductType.product_type_name).all()
    tenders = Tender.query.order_by(Tender.tender_name).all()
    sexes = Sex.query.order_by(Sex.sex_name).all()
    customers = Customer.query.order_by(Customer.customer_name).all()
    transaction_types = TransactionType.query.filter_by(active=True).order_by(TransactionType.sort_order).all()
    from ..ape_batch.models import ApeBatch
    ape_batches = ApeBatch.query.order_by(ApeBatch.batch_date.desc()).all()

    context = {
        "form": form,
        "transaction_type": transaction_type,
        "transaction_types": transaction_types,
        "product_types": product_types,
        "tenders": tenders,
        "sexes": sexes,
        "customers": customers,
        "ape_batches": ape_batches,
        "app_label": app_label,
        "is_new": True,
        "locked_from_batch": locked_from_batch,
    }
    return render_template("daily_sales/new_transaction.html", **context)


# ---------------------------------------------------------------------------
# Edit transaction  (GET: load | POST: update)
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit_transaction(transaction_id):
    if not _can_transact():
        abort(403)
    record = Transaction.query.get_or_404(transaction_id)
    form = Form()
    form.user_prepare_id = current_user.id

    if record.submitted or record.cancelled:
        flash('This transaction is locked and cannot be edited.', 'warning')
        return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))

    if request.method == 'POST':
        form._post(request.form)
        form.id = transaction_id

        action = request.form.get('action', 'save')

        if form._validate_on_submit():
            form._save()

            if action == 'submit':
                form._submit()
                flash('Transaction submitted successfully.', 'success')
                return redirect(url_for(f'{app_name}.view_transaction', transaction_id=form.id))
            else:
                flash('Transaction updated.', 'success')
                return redirect(url_for(f'{app_name}.edit_transaction', transaction_id=form.id))
    else:
        form._populate(record)

    transaction_type = record.transaction_type
    product_types = ProductType.query.order_by(ProductType.product_type_name).all()
    tenders = Tender.query.order_by(Tender.tender_name).all()
    sexes = Sex.query.order_by(Sex.sex_name).all()
    customers = Customer.query.order_by(Customer.customer_name).all()
    transaction_types = TransactionType.query.filter_by(active=True).order_by(TransactionType.sort_order).all()
    from ..ape_batch.models import ApeBatch
    ape_batches = ApeBatch.query.order_by(ApeBatch.batch_date.desc()).all()

    context = {
        "form": form,
        "transaction_type": transaction_type,
        "transaction_types": transaction_types,
        "product_types": product_types,
        "tenders": tenders,
        "sexes": sexes,
        "customers": customers,
        "ape_batches": ape_batches,
        "app_label": app_label,
        "is_new": False,
        "record": record,
    }
    return render_template("daily_sales/new_transaction.html", **context)


# ---------------------------------------------------------------------------
# Guide
# ---------------------------------------------------------------------------

@bp.route('/guide')
@login_required
@roles_accepted([ROLES_ACCEPTED])
def guide():
    return render_template("daily_sales/guide.html")


# ---------------------------------------------------------------------------
# View (read-only)
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def view_transaction(transaction_id):
    record = Transaction.query.get_or_404(transaction_id)
    context = {
        "record": record,
        "app_label": app_label,
    }
    return render_template("daily_sales/view_transaction.html", **context)


# ---------------------------------------------------------------------------
# Cancel
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>/cancel', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel_transaction(transaction_id):
    if not _can_transact():
        abort(403)
    record = Transaction.query.get_or_404(transaction_id)

    if record.cancelled:
        flash('Transaction is already cancelled.', 'warning')
    elif record.submitted:
        flash('Submitted transactions cannot be cancelled here. Contact an admin.', 'danger')
    else:
        form = Form()
        form.id = transaction_id
        form._populate(record)
        form._cancel()
        flash('Transaction cancelled.', 'warning')

    return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))


# ---------------------------------------------------------------------------
# Delete (draft only)
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>/delete', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete_transaction(transaction_id):
    if not _can_transact():
        abort(403)
    record = Transaction.query.get_or_404(transaction_id)

    if record.submitted or record.cancelled:
        flash('Only draft transactions can be deleted.', 'danger')
        return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))

    TransactionDetail.query.filter_by(transaction_id=transaction_id).delete()
    TransactionTender.query.filter_by(transaction_id=transaction_id).delete()

    from .admin_models import UserTransaction, AdminTransaction
    UserTransaction.query.filter_by(transaction_id=transaction_id).delete()
    AdminTransaction.query.filter_by(transaction_id=transaction_id).delete()

    from application.extensions import db
    db.session.delete(record)
    db.session.commit()

    flash('Transaction deleted.', 'success')
    return redirect(url_for(f'{app_name}.home'))


# ---------------------------------------------------------------------------
# Pending approval list  (admin + superuser only)
# ---------------------------------------------------------------------------

@bp.route('/pending_approval', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def pending_approval():
    from sqlalchemy import select as sa_select
    from .admin_models import AdminTransaction
    from flask import abort

    if not (current_user.admin or current_user.superuser):
        abort(403)

    approved_ids = sa_select(AdminTransaction.transaction_id)
    records = (
        Transaction.query
        .filter(
            Transaction.submitted.isnot(None),
            Transaction.submitted != '',
            Transaction.cancelled.is_(None),
            Transaction.id.notin_(approved_ids),
        )
        .order_by(Transaction.record_date.asc(), Transaction.id.asc())
        .all()
    )
    return render_template(
        "daily_sales/pending_approval.html",
        records=records,
        app_label=app_label,
    )


# ---------------------------------------------------------------------------
# Approve transaction  (admin + superuser only)
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>/approve', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def approve_transaction(transaction_id):
    from .admin_models import AdminTransaction
    from application.extensions import db
    from flask import abort

    if not (current_user.admin or current_user.superuser):
        abort(403)

    record = Transaction.query.get_or_404(transaction_id)

    if not record.submitted or record.cancelled:
        flash('Only submitted, active transactions can be approved.', 'warning')
        return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))

    existing = AdminTransaction.query.filter_by(transaction_id=transaction_id).first()
    if existing:
        flash('Transaction is already approved.', 'info')
        return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))

    db.session.add(AdminTransaction(
        transaction_id=transaction_id,
        user_id=current_user.id,
    ))
    db.session.commit()
    flash('Transaction approved.', 'success')
    return redirect(url_for(f'{app_name}.pending_approval'))


# ---------------------------------------------------------------------------
# Unlock transaction  (superuser only)
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>/unlock', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def unlock_transaction(transaction_id):
    from .admin_models import AdminTransaction
    from application.extensions import db
    from flask import abort

    if not current_user.superuser:
        abort(403)

    AdminTransaction.query.filter_by(transaction_id=transaction_id).delete()
    db.session.commit()
    flash('Transaction unlocked and returned to pending approval.', 'warning')
    return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))


# ---------------------------------------------------------------------------
# Customer autocomplete
# ---------------------------------------------------------------------------

@bp.route('/customer/search', methods=['GET'])
@login_required
def customer_search():
    from flask import jsonify
    from ...register.customer import Customer
    q = request.args.get('q', '').strip()
    results = Customer.query.filter(
        Customer.customer_name.ilike(f'%{q}%')
    ).order_by(Customer.customer_name).limit(20).all()
    return jsonify([c.customer_name for c in results])


# ---------------------------------------------------------------------------
# Record deposit
# ---------------------------------------------------------------------------

@bp.route('/deposit/new', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def record_deposit():
    if not _can_transact():
        abort(403)
    if request.method == 'POST':
        # Placeholder: wire to a Deposit model when ready
        flash('Deposit recorded (not yet persisted â€" model pending).', 'info')
        return redirect(url_for(f'{app_name}.record_deposit'))

    return render_template('daily_sales/record_deposit.html', app_label=app_label)


# ---------------------------------------------------------------------------
# Daily report
# ---------------------------------------------------------------------------

@bp.route("/daily_report", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def daily_report():
    from datetime import timedelta

    report_date_str = request.args.get('date', str(ph_today()))
    try:
        curr_date = date.fromisoformat(report_date_str)
    except ValueError:
        curr_date = ph_today()

    prev_date = curr_date - timedelta(days=1)

    def build_report(target_date):
        transactions = Transaction.query.filter(
            Transaction.record_date == str(target_date),
            Transaction.submitted.isnot(None),
            Transaction.cancelled.is_(None),
        ).all()

        report = _Report()
        report.report_date = target_date

        for t in transactions:
            tx_type = t.transaction_type.type_code if t.transaction_type else 'walk_in'
            if tx_type not in report.sales:
                report.sales[tx_type] = {}
            for tender in t.transaction_tenders:
                t_name = tender.tender.tender_name if tender.tender else 'Unknown'
                report.sales[tx_type][t_name] = report.sales[tx_type].get(t_name, 0) + tender.amount

        return report

    prev_report = build_report(prev_date)
    curr_report = build_report(curr_date)

    # Load all active transaction types — highest sort_order first (newest = top)
    transaction_types = TransactionType.query.filter_by(active=True).order_by(TransactionType.sort_order.desc()).all()

    all_tenders = Tender.query.order_by(Tender.sort_order.desc()).all()
    tender_order = {t.tender_name: t.sort_order for t in all_tenders}

    def static_for(type_code):
        return [t.tender_name for t in all_tenders
                if t.report_static and t.transaction_types
                and type_code in t.transaction_types.split(',')]

    def ordered_keys(*dicts, static=None):
        keys = set()
        for d in dicts:
            keys.update(d.keys())
        if static:
            keys.update(static)
        return sorted(keys, key=lambda k: tender_order.get(k, 0), reverse=True)

    receivable_names = {t.tender_name for t in all_tenders if t.is_receivable}

    # Build one section entry per active transaction type
    report_sections = []
    for tt in transaction_types:
        prev_sales = prev_report.sales.get(tt.type_code, {})
        curr_sales = curr_report.sales.get(tt.type_code, {})
        tenders = ordered_keys(prev_sales, curr_sales, static=static_for(tt.type_code))
        curr_receivable = sum(
            amt for name, amt in curr_sales.items() if name in receivable_names
        )
        prev_receivable = sum(
            amt for name, amt in prev_sales.items() if name in receivable_names
        )
        report_sections.append({
            'type_code': tt.type_code,
            'type_name': tt.type_name,
            'tenders': tenders,
            'is_dialysis': tt.type_code == 'dialysis',
            'curr_receivable': curr_receivable,
            'prev_receivable': prev_receivable,
        })

    # Cash on hand = CASH tender across diagnostic sections only (dialysis is Philhealth)
    def cash_total(report):
        return sum(
            sales.get('Cash', 0.0)
            for code, sales in report.sales.items()
            if code != 'dialysis'
        )

    context = {
        "prev_report": prev_report,
        "curr_report": curr_report,
        "report_sections": report_sections,
        "receivable_names": receivable_names,
        "prev_cash": cash_total(prev_report),
        "curr_cash": cash_total(curr_report),
        "app_label": app_label,
        "report_date": curr_date,
        "prev_date": prev_date,
        "next_date": curr_date + timedelta(days=1),
    }
    return render_template("daily_sales/daily_sales_report.html", **context)


# ---------------------------------------------------------------------------
# Internal Report class
# ---------------------------------------------------------------------------

class _Report:
    def __init__(self):
        self.report_date: date = ph_today()
        self.sales: dict = {}  # {type_code: {tender_name: amount}}

    @property
    def total_sales(self):
        return sum(sum(v.values()) for v in self.sales.values())

    @property
    def total_diagnostic_sales(self):
        return sum(
            sum(v.values()) for code, v in self.sales.items() if code != 'dialysis'
        )

    @property
    def total_dialysis_sales(self):
        return sum(self.sales.get('dialysis', {}).values())

