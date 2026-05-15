from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import date
from sqlalchemy import func

from ...user import login_required, roles_accepted, current_user
from ...register.customer import Customer

from . import app_label, app_name
from .models import Transaction, TransactionDetail, TransactionTender
from .forms import Form
from ...register.product_type import ProductType
from ...register.tender import Tender
from ...register.sex.models import Sex

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


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
    today_str = str(date.today())

    transactions = Transaction.query.filter(
        Transaction.record_date == today_str
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

    context = {
        "app_label": app_label,
        "today": date.today(),
        "summary": summary,
        "transactions": transactions,
        "txn_type_tenders": txn_type_tenders,
    }
    return render_template("daily_sales/home.html", **context)


# ---------------------------------------------------------------------------
# New transaction  (GET: show form | POST: save)
# ---------------------------------------------------------------------------

@bp.route('/transaction/new', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_transaction():
    transaction_type = request.args.get('type', 'walk_in')
    form = Form()
    form.user_prepare_id = current_user.id
    form.record_date = str(date.today())  # default to today
    form.record_number = _generate_record_number()

    if request.method == 'POST':
        form._post(request.form)
        # Always auto-assign record number â€” user cannot edit it
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

    context = {
        "form": form,
        "transaction_type": transaction_type,
        "product_types": product_types,
        "tenders": tenders,
        "sexes": sexes,
        "customers": customers,
        "app_label": app_label,
        "is_new": True,
    }
    return render_template("daily_sales/new_transaction.html", **context)


# ---------------------------------------------------------------------------
# Edit transaction  (GET: load | POST: update)
# ---------------------------------------------------------------------------

@bp.route('/transaction/<int:transaction_id>/edit', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit_transaction(transaction_id):
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

    transaction_type = record.description or 'walk_in'
    product_types = ProductType.query.order_by(ProductType.product_type_name).all()
    tenders = Tender.query.order_by(Tender.tender_name).all()
    sexes = Sex.query.order_by(Sex.sex_name).all()
    customers = Customer.query.order_by(Customer.customer_name).all()

    context = {
        "form": form,
        "transaction_type": transaction_type,
        "product_types": product_types,
        "tenders": tenders,
        "sexes": sexes,
        "customers": customers,
        "app_label": app_label,
        "is_new": False,
        "record": record,
    }
    return render_template("daily_sales/new_transaction.html", **context)


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
    if request.method == 'POST':
        # Placeholder: wire to a Deposit model when ready
        flash('Deposit recorded (not yet persisted â€” model pending).', 'info')
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

    report_date_str = request.args.get('date', str(date.today()))
    try:
        curr_date = date.fromisoformat(report_date_str)
    except ValueError:
        curr_date = date.today()

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
            gross = sum(d.amount - d.discount for d in t.transaction_details)
            net = gross - (t.discount or 0)

            tx_type = (t.description or '').lower()

            for tender in t.transaction_tenders:
                t_name = tender.tender.tender_name if tender.tender else 'Unknown'
                amount = tender.amount

                if 'hmo' in tx_type or 'ape' in tx_type:
                    report.hmo_sales[t_name] = report.hmo_sales.get(t_name, 0) + amount
                elif 'home' in tx_type:
                    report.home_service_sales[t_name] = report.home_service_sales.get(t_name, 0) + amount
                elif 'dialysis' in tx_type:
                    report.dialysis_sales[t_name] = report.dialysis_sales.get(t_name, 0) + amount
                else:
                    report.walk_in_sales[t_name] = report.walk_in_sales.get(t_name, 0) + amount

        report.total_diagnostic_sales = (
            sum(report.hmo_sales.values()) +
            sum(report.home_service_sales.values()) +
            sum(report.walk_in_sales.values())
        )
        report.total_dialysis_sales = sum(report.dialysis_sales.values())
        return report

    prev_report = build_report(prev_date)
    curr_report = build_report(curr_date)

    # Collect all tender names used across both days for HMO section
    all_tender_names = Tender.query.order_by(Tender.tender_name).all()
    hmos = [{"hmo_name": t.tender_name, "receivable": "0.00"} for t in all_tender_names]

    context = {
        "prev_report": prev_report,
        "curr_report": curr_report,
        "hmos": hmos,
        "app_label": app_label,
        "report_date": curr_date,
    }
    return render_template("daily_sales/daily_sales_report.html", **context)


# ---------------------------------------------------------------------------
# Internal Report class
# ---------------------------------------------------------------------------

class _Report:
    def __init__(self):
        self.report_date: date = date.today()
        self.hmo_sales: dict = {}
        self.home_service_sales: dict = {}
        self.walk_in_sales: dict = {}
        self.dialysis_sales: dict = {}
        self.total_diagnostic_sales: float = 0.0
        self.total_dialysis_sales: float = 0.0

    @property
    def total_sales(self):
        return self.total_diagnostic_sales + self.total_dialysis_sales

