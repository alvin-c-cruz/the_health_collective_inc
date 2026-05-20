from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import date, datetime
from sqlalchemy import func

from ...user import login_required, roles_accepted, current_user
from ...register.customer import Customer
from application.extensions import db, ph_today
from ..bank_account.models import BankAccount

from . import app_label, app_name
from .models import (Transaction, TransactionDetail, TransactionTender, TransactionType, Deposit, DepositItem,
                     FundCategory, FundReceived, FundDisbursed, PettyCashVoucher, Payee,
                     ReimbursementReport, ReimbursementReceived)
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

    # Get count of pending change requests for admins
    from .change_request_models import ChangeRequest
    pending_change_requests_count = ChangeRequest.query.filter_by(status='pending').count()

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
        "pending_change_requests_count": pending_change_requests_count,
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
    elif transaction_type and transaction_type.type_code == 'ape':
        # Default tender to Credit for all APE transactions
        credit_tender = Tender.query.filter(
            Tender.tender_name.ilike('credit')
        ).first()
        if credit_tender:
            form.tenders[0][1].tender_id = credit_tender.id
            # If locked from a batch, also pre-fill the package amount
            if locked_from_batch and ape_batch_id_arg:
                from ..ape_batch.models import ApeBatch
                batch = ApeBatch.query.get(ape_batch_id_arg)
                if batch and batch.package_amount:
                    form.tenders[0][1].amount = batch.package_amount

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


@bp.route('/transaction/<int:transaction_id>/uncancel', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def uncancel_transaction(transaction_id):
    """Un-cancel a transaction - only allowed before submission"""
    record = Transaction.query.get_or_404(transaction_id)

    if not record.cancelled:
        flash('Transaction is not cancelled.', 'warning')
    elif record.submitted:
        flash('Submitted transactions cannot be un-cancelled. Contact an admin.', 'danger')
    else:
        form = Form()
        form.id = transaction_id
        form._populate(record)
        success = form._uncancel()
        if success:
            flash('Transaction un-cancelled successfully.', 'success')
        else:
            flash('Unable to un-cancel this transaction.', 'danger')

    return redirect(url_for(f'{app_name}.view_transaction', transaction_id=transaction_id))


# ---------------------------------------------------------------------------
# Bulk submit (APE batch page)
# ---------------------------------------------------------------------------

@bp.route('/transaction/bulk_submit', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def bulk_submit():
    if not _can_transact():
        abort(403)
    ids = request.form.getlist('transaction_ids')
    batch_id = request.form.get('batch_id', type=int)
    submitted_count = 0
    for tid in ids:
        record = Transaction.query.get(int(tid))
        if record and not record.submitted and not record.cancelled:
            record.submitted = str(ph_today())
            submitted_count += 1
    db.session.commit()
    if submitted_count:
        flash(f'{submitted_count} transaction(s) submitted successfully.', 'success')
    else:
        flash('No eligible draft transactions were selected.', 'warning')
    if batch_id:
        from ..ape_batch.views import bp as ape_bp
        return redirect(url_for('ape_batch.view_batch', batch_id=batch_id))
    return redirect(url_for(f'{app_name}.home'))


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

def get_undeposited_cash_transactions():
    """Get all transactions with cash payments that haven't been deposited yet"""
    from .models import Deposit, DepositItem
    from application.blueprints.register.tender.models import Tender
    from sqlalchemy import desc

    # Get all submitted transactions
    transactions = Transaction.query.filter(
        Transaction.submitted.isnot(None),
        Transaction.cancelled.is_(None)
    ).order_by(desc(Transaction.id)).all()  # Use ID for ordering to avoid date comparison issues

    # Filter transactions that have cash tenders
    undeposited = []
    for transaction in transactions:
        # Calculate cash amount for this transaction
        cash_amount = sum(
            td.amount for td in transaction.transaction_tenders
            if td.tender and 'cash' in td.tender.tender_name.lower()
        )

        if cash_amount <= 0:
            continue

        # Check if already deposited (only count posted deposits)
        deposited_amount = sum(
            item.amount for item in transaction.deposit_items
            if item.deposit.status == 'posted'  # Only count posted deposits
        )

        remaining_cash = cash_amount - deposited_amount

        # Only include if remaining cash is greater than 0.01 (to avoid floating point precision issues)
        if remaining_cash > 0.01:
            undeposited.append({
                'transaction': transaction,
                'cash_amount': cash_amount,
                'deposited_amount': deposited_amount,
                'remaining_cash': remaining_cash,
            })

    return undeposited


@bp.route('/deposit/new', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def record_deposit():
    if not _can_transact():
        abort(403)

    from .models import Deposit, DepositItem
    from flask_login import current_user
    from application.blueprints.operations.bank_account.models import BankAccount

    if request.method == 'POST':
        try:
            # Create new deposit
            deposit = Deposit()
            deposit.record_date = request.form.get('record_date')
            deposit.reference_number = request.form.get('reference_number', '')
            deposit.bank_account = request.form.get('bank_account', '')
            deposit.notes = request.form.get('notes', '')
            deposit.status = 'draft'  # Deposits start as draft
            deposit.created_by_id = current_user.id
            deposit.created_at = datetime.now()

            db.session.add(deposit)
            db.session.flush()  # Get deposit ID

            # Add deposit items from selected transactions
            total_amount = 0
            transaction_ids = request.form.getlist('transaction_ids')

            for trans_id in transaction_ids:
                amount = float(request.form.get(f'amount_{trans_id}', 0))
                if amount > 0:
                    item = DepositItem()
                    item.deposit_id = deposit.id
                    item.transaction_id = int(trans_id)
                    item.amount = amount
                    db.session.add(item)
                    total_amount += amount

            db.session.commit()

            flash(f'Deposit recorded successfully! Total amount: ₱{total_amount:,.2f}', 'success')
            return redirect(url_for(f'{app_name}.deposit_report'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error recording deposit: {str(e)}', 'danger')
            return redirect(url_for(f'{app_name}.record_deposit'))

    # GET request - show form
    undeposited_transactions = get_undeposited_cash_transactions()
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()

    context = {
        'app_label': app_label,
        'undeposited_transactions': undeposited_transactions,
        'bank_accounts': bank_accounts,
    }

    return render_template('daily_sales/record_deposit.html', **context)


# ---------------------------------------------------------------------------
# Daily report
# ---------------------------------------------------------------------------

@bp.route('/deposit/report', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def deposit_report():
    """Deposit report - summary of all deposits arranged by date"""
    from sqlalchemy import desc

    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Build query - show all deposits including cancelled
    query = Deposit.query

    if start_date:
        query = query.filter(Deposit.record_date >= start_date)
    if end_date:
        query = query.filter(Deposit.record_date <= end_date)

    # Get all deposits ordered by date (most recent first)
    deposits = query.order_by(desc(Deposit.record_date), desc(Deposit.id)).all()

    # Calculate totals (exclude cancelled deposits from totals)
    total_deposits = len([d for d in deposits if d.status != 'cancelled'])
    total_amount = sum(deposit.total_amount for deposit in deposits if deposit.status != 'cancelled')

    context = {
        'app_label': app_label,
        'deposits': deposits,
        'total_deposits': total_deposits,
        'total_amount': total_amount,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render_template(f'{app_name}/deposit_report.html', **context)


@bp.route('/deposit/view/<int:deposit_id>', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def view_deposit(deposit_id):
    """View deposit details"""
    deposit = Deposit.query.get_or_404(deposit_id)

    context = {
        'app_label': app_label,
        'deposit': deposit,
    }

    return render_template(f'{app_name}/view_deposit.html', **context)


@bp.route('/deposit/submit/<int:deposit_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def submit_deposit(deposit_id):
    """Submit deposit for approval"""
    deposit = Deposit.query.get_or_404(deposit_id)

    # Only draft deposits can be submitted
    if deposit.status != 'draft':
        flash('Only draft deposits can be submitted.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_report'))

    # Check if user is the creator
    if deposit.created_by_id != current_user.id:
        flash('You can only submit your own deposits.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_report'))

    # Admin auto-approve: If user is admin, automatically approve deposit
    if current_user.is_admin:
        deposit.status = 'posted'
        deposit.submitted_by_id = current_user.id
        deposit.submitted_at = datetime.now()
        deposit.approved_by_id = current_user.id
        deposit.approved_at = datetime.now()
        deposit.updated_at = datetime.now()

        db.session.commit()

        flash(f'Deposit auto-approved and posted! Total amount: ₱{deposit.formatted_total_amount}', 'success')
    else:
        # Regular user: submit for approval
        deposit.status = 'submitted'
        deposit.submitted_by_id = current_user.id
        deposit.submitted_at = datetime.now()
        deposit.updated_at = datetime.now()

        db.session.commit()

        flash(f'Deposit submitted successfully! Waiting for admin approval. Total amount: ₱{deposit.formatted_total_amount}', 'success')

    return redirect(url_for(f'{app_name}.deposit_report'))


@bp.route('/transaction/reject/<int:transaction_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def reject_transaction(transaction_id):
    """Reject submitted transaction - send back to draft"""
    transaction = Transaction.query.get_or_404(transaction_id)

    # Only submitted transactions can be rejected
    if not transaction.submitted:
        flash('Only submitted transactions can be rejected.', 'danger')
        return redirect(url_for('daily_sales.change_requests_list'))

    # Clear submitted status to send back to draft
    transaction.submitted = None
    transaction.updated_at = datetime.now()

    db.session.commit()

    flash(f'Transaction #{transaction.id} rejected and sent back to draft.', 'warning')
    return redirect(url_for('daily_sales.change_requests_list'))


@bp.route('/deposit/approve/<int:deposit_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def approve_deposit(deposit_id):
    """Approve submitted deposit (admin only)"""
    deposit = Deposit.query.get_or_404(deposit_id)

    # Only submitted deposits can be approved
    if deposit.status != 'submitted':
        flash('Only submitted deposits can be approved.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_report'))

    deposit.status = 'posted'
    deposit.approved_by_id = current_user.id
    deposit.approved_at = datetime.now()
    deposit.updated_at = datetime.now()

    db.session.commit()

    flash(f'Deposit approved successfully! Total amount: ₱{deposit.formatted_total_amount}', 'success')
    return redirect(url_for(f'{app_name}.deposit_report'))


@bp.route('/deposit/reject/<int:deposit_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def reject_deposit(deposit_id):
    """Reject submitted deposit - send back to draft"""
    deposit = Deposit.query.get_or_404(deposit_id)

    # Only submitted deposits can be rejected
    if deposit.status != 'submitted':
        flash('Only submitted deposits can be rejected.', 'danger')
        return redirect(url_for('daily_sales.change_requests_list'))

    # Send back to draft
    deposit.status = 'draft'
    deposit.updated_at = datetime.now()

    db.session.commit()

    flash(f'Deposit #{deposit.id} rejected and sent back to draft.', 'warning')
    return redirect(url_for('daily_sales.change_requests_list'))


@bp.route('/deposit/cancel/<int:deposit_id>', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel_deposit(deposit_id):
    """Cancel draft deposit (soft delete - marks as cancelled)"""
    deposit = Deposit.query.get_or_404(deposit_id)

    # Only draft deposits can be cancelled
    if deposit.status != 'draft':
        flash('Only draft deposits can be cancelled.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_report'))

    # Check if user is the creator
    if deposit.created_by_id != current_user.id:
        flash('You can only cancel your own deposits.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_report'))

    # Get cancellation reason from form
    cancellation_reason = request.form.get('cancellation_reason', '').strip()

    if not cancellation_reason:
        flash('Cancellation reason is required.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_report'))

    # Soft delete - mark as cancelled instead of deleting
    deposit.status = 'cancelled'
    deposit.cancelled_by_id = current_user.id
    deposit.cancelled_at = datetime.now()
    deposit.cancellation_reason = cancellation_reason
    deposit.updated_at = datetime.now()

    db.session.commit()

    flash('Deposit cancelled successfully.', 'info')
    return redirect(url_for(f'{app_name}.deposit_report'))


# ---------------------------------------------------------------------------
# Change Requests for Deposits
# ---------------------------------------------------------------------------

@bp.route('/deposit/request-change/<int:deposit_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def request_deposit_change(deposit_id):
    """Staff/supervisor requests change to a posted deposit"""
    from .change_request_models import ChangeRequest

    deposit = Deposit.query.get_or_404(deposit_id)

    # Only submitted or posted deposits can have change requests
    if deposit.status not in ['submitted', 'posted']:
        flash('Only submitted or posted deposits can have change requests.', 'danger')
        return redirect(url_for(f'{app_name}.view_deposit', deposit_id=deposit_id))

    if request.method == 'POST':
        # Capture old values
        old_values = {
            'record_date': deposit.record_date,
            'bank_account': deposit.bank_account,
            'reference_number': deposit.reference_number,
            'notes': deposit.notes,
        }

        # Capture new values from form
        new_values = {
            'record_date': request.form.get('record_date', ''),
            'bank_account': request.form.get('bank_account', ''),
            'reference_number': request.form.get('reference_number', ''),
            'notes': request.form.get('notes', ''),
        }

        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the change request.', 'danger')
            return redirect(url_for(f'{app_name}.request_deposit_change', deposit_id=deposit_id))

        # Create change request
        cr = ChangeRequest()
        cr.record_type = 'deposit'
        cr.record_id = deposit_id
        cr.old_values = old_values
        cr.new_values = new_values
        cr.reason = reason
        cr.status = 'pending'
        cr.requested_by_id = current_user.id
        cr.requested_at = datetime.now()

        db.session.add(cr)
        db.session.commit()

        flash('Change request submitted successfully. Waiting for admin approval.', 'success')
        return redirect(url_for(f'{app_name}.view_deposit', deposit_id=deposit_id))

    # GET request - show form
    # Get undeposited transaction tenders for potential addition
    from .models import TransactionTender, Transaction, DepositItem

    # Get IDs of transactions already in ANY deposit
    deposited_transaction_ids = db.session.query(DepositItem.transaction_id).distinct().all()
    deposited_transaction_ids = [tid[0] for tid in deposited_transaction_ids]

    # Query for ALL undeposited tenders (not just same date)
    undeposited_tenders = TransactionTender.query.join(Transaction).filter(
        TransactionTender.tender_id.in_([1, 2]),  # Cash and checks typically
        ~Transaction.id.in_(deposited_transaction_ids) if deposited_transaction_ids else True,  # Not in any deposit
        Transaction.submitted != None,
        Transaction.cancelled == None
    ).order_by(Transaction.record_date.desc()).all()

    context = {
        'app_label': app_label,
        'deposit': deposit,
        'undeposited_tenders': undeposited_tenders,
    }

    return render_template(f'{app_name}/request_deposit_change.html', **context)


@bp.route('/deposit/request-cancellation/<int:deposit_id>', methods=['GET', 'POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def request_deposit_cancellation(deposit_id):
    """Staff/supervisor requests cancellation of a posted deposit"""
    from .change_request_models import ChangeRequest

    deposit = Deposit.query.get_or_404(deposit_id)

    # Can only request cancellation on posted deposits
    if deposit.status != 'posted':
        flash('Can only request cancellation on posted deposits.', 'warning')
        return redirect(url_for(f'{app_name}.view_deposit', deposit_id=deposit_id))

    # Check if there's already a pending cancellation request
    existing_request = ChangeRequest.query.filter_by(
        record_type='deposit',
        record_id=deposit.id,
        request_action='cancellation',
        status='pending'
    ).first()

    if existing_request:
        flash('There is already a pending cancellation request for this deposit.', 'warning')
        return redirect(url_for(f'{app_name}.view_deposit', deposit_id=deposit_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the cancellation request.', 'warning')
            context = {
                'app_label': app_label,
                'deposit': deposit,
            }
            return render_template(f'{app_name}/request_deposit_cancellation.html', **context)

        # Create cancellation request
        cr = ChangeRequest()
        cr.record_type = 'deposit'
        cr.record_id = deposit_id
        cr.request_action = 'cancellation'
        cr.reason = reason
        cr.status = 'pending'
        cr.requested_by_id = current_user.id
        cr.requested_at = datetime.now()
        cr.old_values = {}
        cr.new_values = {}

        db.session.add(cr)
        db.session.commit()

        flash('Cancellation request submitted. An admin will review it.', 'success')
        return redirect(url_for(f'{app_name}.view_deposit', deposit_id=deposit_id))

    context = {
        'app_label': app_label,
        'deposit': deposit,
    }

    return render_template(f'{app_name}/request_deposit_cancellation.html', **context)


@bp.route('/deposit/change-requests', methods=['GET'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def deposit_change_requests():
    """Admin views pending deposit change requests"""
    from .change_request_models import ChangeRequest

    # Get all pending change requests for deposits
    change_requests = ChangeRequest.query.filter(
        ChangeRequest.record_type == 'deposit',
        ChangeRequest.status == 'pending'
    ).order_by(ChangeRequest.requested_at.desc()).all()

    context = {
        'app_label': app_label,
        'change_requests': change_requests,
    }

    return render_template(f'{app_name}/deposit_change_requests.html', **context)


@bp.route('/deposit/change-requests/<int:cr_id>/review', methods=['POST'])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def review_deposit_change_request(cr_id):
    """Admin approves or rejects deposit change request"""
    from .change_request_models import ChangeRequest

    cr = ChangeRequest.query.get_or_404(cr_id)

    # Only pending requests can be reviewed
    if cr.status != 'pending':
        flash('This change request has already been reviewed.', 'warning')
        return redirect(url_for(f'{app_name}.deposit_change_requests'))

    action = request.form.get('action')  # 'approve' or 'reject'
    review_notes = request.form.get('review_notes', '').strip()

    if action == 'approve':
        # Apply the changes to the deposit
        deposit = Deposit.query.get(cr.record_id)
        if deposit:
            nv = cr.new_values
            deposit.record_date = nv.get('record_date') or deposit.record_date
            deposit.bank_account = nv.get('bank_account')
            deposit.reference_number = nv.get('reference_number')
            deposit.notes = nv.get('notes')
            deposit.updated_at = datetime.now()

            # Set deposit back to submitted status for re-approval
            deposit.status = 'submitted'
            deposit.submitted_by_id = current_user.id
            deposit.submitted_at = datetime.now()

        cr.status = 'approved'
        flash('Change request approved. Deposit updated and set to submitted status for re-approval.', 'success')

    elif action == 'reject':
        cr.status = 'rejected'
        flash('Change request rejected.', 'info')

    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for(f'{app_name}.deposit_change_requests'))

    # Record review details
    cr.reviewed_by_id = current_user.id
    cr.reviewed_at = datetime.now()
    cr.review_notes = review_notes

    db.session.commit()

    return redirect(url_for(f'{app_name}.deposit_change_requests'))


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

    # Build one section entry per active transaction type
    report_sections = []
    for tt in transaction_types:
        prev_sales = prev_report.sales.get(tt.type_code, {})
        curr_sales = curr_report.sales.get(tt.type_code, {})
        tenders = ordered_keys(prev_sales, curr_sales, static=static_for(tt.type_code))

        report_sections.append({
            'type_code': tt.type_code,
            'type_name': tt.type_name,
            'tenders': tenders,
            'is_dialysis': tt.type_code == 'dialysis',
        })

    # Cash on hand = CASH tender across diagnostic sections only (dialysis is Philhealth)
    def cash_total(report):
        return sum(
            sales.get('Cash', 0.0)
            for code, sales in report.sales.items()
            if code != 'dialysis'
        )

    # Calculate fund movements for display in "Cash on Hand" section (daily amounts)
    def calculate_daily_fund_movements(target_date):
        """Calculate fund received and disbursed for a specific date only"""
        funds_received = FundReceived.query.filter(
            FundReceived.record_date == str(target_date),
            FundReceived.status == 'posted'
        ).all()

        funds_disbursed = FundDisbursed.query.filter(
            FundDisbursed.record_date == str(target_date),
            FundDisbursed.status == 'posted'
        ).all()

        total_received = sum(f.amount for f in funds_received)
        total_disbursed = sum(f.amount for f in funds_disbursed)

        return {
            'total_received': total_received,
            'total_disbursed': total_disbursed,
        }

    # Calculate running balances for "Accountabilities" section (cumulative up to date)
    def calculate_fund_running_balance(target_date):
        """Calculate running balance for each fund category as of target_date"""
        # Get all fund transactions up to and including target_date
        funds_received = FundReceived.query.filter(
            FundReceived.record_date <= str(target_date),
            FundReceived.status == 'posted'
        ).all()

        funds_disbursed = FundDisbursed.query.filter(
            FundDisbursed.record_date <= str(target_date),
            FundDisbursed.status == 'posted'
        ).all()

        # Calculate running balance by category
        balance_by_category = {}
        for fr in funds_received:
            cat_name = fr.fund_category.category_name if fr.fund_category else 'Unknown'
            balance_by_category[cat_name] = balance_by_category.get(cat_name, 0) + fr.amount

        for fd in funds_disbursed:
            cat_name = fd.fund_category.category_name if fd.fund_category else 'Unknown'
            balance_by_category[cat_name] = balance_by_category.get(cat_name, 0) - fd.amount

        return balance_by_category

    # Calculate undeposited cash sales running balance
    def calculate_undeposited_cash(target_date):
        """Calculate running balance of undeposited cash sales as of target_date"""
        # Get all cash sales up to and including target_date
        cash_sales = Transaction.query.filter(
            Transaction.record_date <= str(target_date),
            Transaction.submitted.isnot(None),
            Transaction.cancelled.is_(None)
        ).all()

        total_cash = 0
        for txn in cash_sales:
            for tender in txn.transaction_tenders:
                if tender.tender and 'cash' in tender.tender.tender_name.lower():
                    # Only count diagnostics cash (not dialysis)
                    if txn.transaction_type and txn.transaction_type.type_code != 'dialysis':
                        total_cash += tender.amount

        # Subtract all posted deposits up to and including target_date
        deposits = Deposit.query.filter(
            Deposit.record_date <= str(target_date),
            Deposit.status == 'posted'
        ).all()

        total_deposited = sum(d.total_amount for d in deposits)

        return total_cash - total_deposited

    # Calculate cash deposited for a specific date
    def calculate_cash_deposited(target_date):
        """Calculate total cash deposited on a specific date"""
        deposits = Deposit.query.filter(
            Deposit.record_date == str(target_date),
            Deposit.status == 'posted'
        ).all()
        return sum(d.total_amount for d in deposits)

    # Calculate beginning cash balance (ending cash from previous date)
    def calculate_cash_on_hand(target_date):
        """
        Calculate cash on hand balance as of target_date
        Formula: Fund balances + Undeposited cash sales
        """
        fund_balances = calculate_fund_running_balance(target_date)
        undeposited = calculate_undeposited_cash(target_date)
        total_funds = sum(fund_balances.values())
        return total_funds + undeposited

    prev_daily_funds = calculate_daily_fund_movements(prev_date)
    curr_daily_funds = calculate_daily_fund_movements(curr_date)

    prev_fund_balances = calculate_fund_running_balance(prev_date)
    curr_fund_balances = calculate_fund_running_balance(curr_date)

    prev_undeposited = calculate_undeposited_cash(prev_date)
    curr_undeposited = calculate_undeposited_cash(curr_date)

    # Calculate cash deposited on each date
    prev_cash_deposited = calculate_cash_deposited(prev_date)
    curr_cash_deposited = calculate_cash_deposited(curr_date)

    # Calculate beginning and ending cash
    # Beginning cash for prev_date = ending cash from day before prev_date
    from datetime import timedelta
    day_before_prev = prev_date - timedelta(days=1)
    prev_beginning_cash = calculate_cash_on_hand(day_before_prev)
    prev_ending_cash = calculate_cash_on_hand(prev_date)

    # Beginning cash for curr_date = ending cash from prev_date
    curr_beginning_cash = prev_ending_cash
    curr_ending_cash = calculate_cash_on_hand(curr_date)

    # Get all fund categories for display
    fund_categories = FundCategory.query.filter_by(active=True).order_by(FundCategory.sort_order).all()

    context = {
        "prev_report": prev_report,
        "curr_report": curr_report,
        "report_sections": report_sections,
        "prev_cash": cash_total(prev_report),
        "curr_cash": cash_total(curr_report),
        "prev_daily_funds": prev_daily_funds,
        "curr_daily_funds": curr_daily_funds,
        "prev_fund_balances": prev_fund_balances,
        "curr_fund_balances": curr_fund_balances,
        "prev_undeposited": prev_undeposited,
        "curr_undeposited": curr_undeposited,
        "prev_cash_deposited": prev_cash_deposited,
        "curr_cash_deposited": curr_cash_deposited,
        "prev_beginning_cash": prev_beginning_cash,
        "curr_beginning_cash": curr_beginning_cash,
        "prev_ending_cash": prev_ending_cash,
        "curr_ending_cash": curr_ending_cash,
        "fund_categories": fund_categories,
        "app_label": app_label,
        "report_date": curr_date,
        "prev_date": prev_date,
        "next_date": curr_date + timedelta(days=1),
    }
    return render_template("daily_sales/daily_sales_report.html", **context)


@bp.route("/sales_summary_report", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def sales_summary_report():
    """
    Sales Summary Report - categorized by service type (Dialysis/Diagnostics)
    and transaction type (Walk-in, Home Service, etc.) with date range picker
    """
    from datetime import timedelta
    from ...register.product import Product

    # Get date range from query params or default to current month
    today = date.today()
    start_date_str = request.args.get('start_date', str(date(today.year, today.month, 1)))
    end_date_str = request.args.get('end_date', str(today))

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        start_date = date(today.year, today.month, 1)
        end_date = today

    # Ensure start_date <= end_date
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Query transactions in date range
    transactions = Transaction.query.filter(
        Transaction.record_date >= str(start_date),
        Transaction.record_date <= str(end_date),
        Transaction.submitted.isnot(None),
        Transaction.cancelled.is_(None),
    ).all()

    # Get products for categorization
    dialysis_product = Product.query.filter(
        (Product.product_name == 'Dialysis') |
        (Product.product_name == 'HEMO DIALYSIS')
    ).first()

    # Build sales data structure:
    # sales[service_type][transaction_type][tender_name] = amount
    sales_data = {
        'Dialysis': {},      # Dialysis services
        'Diagnostics': {},   # All other services (Various Services, etc.)
    }

    # Get all transaction types
    transaction_types = TransactionType.query.filter_by(active=True).order_by(
        TransactionType.sort_order.desc()
    ).all()

    # Initialize structure
    for tt in transaction_types:
        sales_data['Dialysis'][tt.type_code] = {}
        sales_data['Diagnostics'][tt.type_code] = {}

    # Process transactions
    for txn in transactions:
        txn_type_code = txn.transaction_type.type_code if txn.transaction_type else 'walk_in'

        # Determine if this transaction has dialysis services
        is_dialysis = False
        if dialysis_product and txn.transaction_details:
            is_dialysis = any(
                detail.product_id == dialysis_product.id
                for detail in txn.transaction_details
            )

        service_category = 'Dialysis' if is_dialysis else 'Diagnostics'

        # Add tender amounts
        for tender_record in txn.transaction_tenders:
            tender_name = tender_record.tender.tender_name if tender_record.tender else 'Unknown'

            if txn_type_code not in sales_data[service_category]:
                sales_data[service_category][txn_type_code] = {}

            current_amount = sales_data[service_category][txn_type_code].get(tender_name, 0)
            sales_data[service_category][txn_type_code][tender_name] = current_amount + tender_record.amount

    # Calculate totals
    totals = {
        'Dialysis': {},
        'Diagnostics': {},
        'grand_total': 0,
    }

    for service_type in ['Dialysis', 'Diagnostics']:
        service_total = 0
        for txn_type_code in sales_data[service_type]:
            txn_type_total = sum(sales_data[service_type][txn_type_code].values())
            totals[service_type][txn_type_code] = txn_type_total
            service_total += txn_type_total
        totals[service_type]['total'] = service_total
        totals['grand_total'] += service_total

    # Get all tenders for consistent ordering
    all_tenders = Tender.query.order_by(Tender.sort_order.desc()).all()
    tender_order = {t.tender_name: t.sort_order for t in all_tenders}

    # Get unique tenders used in this report
    all_tender_names = set()
    for service_type in sales_data:
        for txn_type in sales_data[service_type]:
            all_tender_names.update(sales_data[service_type][txn_type].keys())

    # Sort tenders by their sort_order
    sorted_tenders = sorted(all_tender_names, key=lambda t: tender_order.get(t, 0), reverse=True)

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'transaction_types': transaction_types,
        'sales_data': sales_data,
        'totals': totals,
        'sorted_tenders': sorted_tenders,
        'app_label': app_label,
        'transaction_count': len(transactions),
        'generated_at': datetime.now(),
    }

    return render_template("daily_sales/sales_summary_report.html", **context)


@bp.route("/sales_summary_excel", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def sales_summary_excel():
    """Export sales summary report to Excel"""
    from datetime import timedelta
    from ...register.product import Product
    import io
    from flask import send_file
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    except ImportError:
        flash('openpyxl library not installed. Cannot export to Excel.', 'danger')
        return redirect(url_for('daily_sales.sales_summary_report'))

    # Get date range from query params
    today = date.today()
    start_date_str = request.args.get('start_date', str(date(today.year, today.month, 1)))
    end_date_str = request.args.get('end_date', str(today))

    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        start_date = date(today.year, today.month, 1)
        end_date = today

    if start_date > end_date:
        start_date, end_date = end_date, start_date

    # Query transactions (same logic as report)
    transactions = Transaction.query.filter(
        Transaction.record_date >= str(start_date),
        Transaction.record_date <= str(end_date),
        Transaction.submitted.isnot(None),
        Transaction.cancelled.is_(None),
    ).all()

    dialysis_product = Product.query.filter(
        (Product.product_name == 'Dialysis') |
        (Product.product_name == 'HEMO DIALYSIS')
    ).first()

    sales_data = {'Dialysis': {}, 'Diagnostics': {}}
    transaction_types = TransactionType.query.filter_by(active=True).order_by(
        TransactionType.sort_order.desc()
    ).all()

    for tt in transaction_types:
        sales_data['Dialysis'][tt.type_code] = {}
        sales_data['Diagnostics'][tt.type_code] = {}

    for txn in transactions:
        txn_type_code = txn.transaction_type.type_code if txn.transaction_type else 'walk_in'
        is_dialysis = False
        if dialysis_product and txn.transaction_details:
            is_dialysis = any(detail.product_id == dialysis_product.id for detail in txn.transaction_details)

        service_category = 'Dialysis' if is_dialysis else 'Diagnostics'

        for tender_record in txn.transaction_tenders:
            tender_name = tender_record.tender.tender_name if tender_record.tender else 'Unknown'
            if txn_type_code not in sales_data[service_category]:
                sales_data[service_category][txn_type_code] = {}
            current_amount = sales_data[service_category][txn_type_code].get(tender_name, 0)
            sales_data[service_category][txn_type_code][tender_name] = current_amount + tender_record.amount

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Sales Summary"

    # Styles
    header_font = Font(bold=True, size=12)
    title_font = Font(bold=True, size=14)
    section_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    section_font = Font(bold=True, color="FFFFFF")
    total_fill = PatternFill(start_color="E7E6E6", end_color="E7E6E6", fill_type="solid")
    border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )

    # Title
    ws['A1'] = 'Sales Summary Report'
    ws['A1'].font = title_font
    ws['A2'] = f'{start_date.strftime("%B %d, %Y")} - {end_date.strftime("%B %d, %Y")}'
    ws['A3'] = f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}'

    # Get tenders
    all_tenders = Tender.query.order_by(Tender.sort_order.desc()).all()
    tender_order = {t.tender_name: t.sort_order for t in all_tenders}
    all_tender_names = set()
    for service_type in sales_data:
        for txn_type in sales_data[service_type]:
            all_tender_names.update(sales_data[service_type][txn_type].keys())
    sorted_tenders = sorted(all_tender_names, key=lambda t: tender_order.get(t, 0), reverse=True)

    row = 5

    # For each service type
    for service_type in ['Diagnostics', 'Dialysis']:
        # Service type header
        ws.cell(row, 1, service_type).font = section_font
        ws.cell(row, 1).fill = section_fill
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(sorted_tenders)+2)
        row += 1

        # Column headers
        ws.cell(row, 1, 'Transaction Type').font = header_font
        for col_idx, tender in enumerate(sorted_tenders, start=2):
            ws.cell(row, col_idx, tender).font = header_font
        ws.cell(row, len(sorted_tenders)+2, 'Total').font = header_font
        row += 1

        # Transaction type rows
        service_total = 0
        for tt in transaction_types:
            if tt.type_code in sales_data[service_type]:
                ws.cell(row, 1, tt.type_name)
                row_total = 0
                for col_idx, tender in enumerate(sorted_tenders, start=2):
                    amount = sales_data[service_type][tt.type_code].get(tender, 0)
                    if amount > 0:
                        ws.cell(row, col_idx, amount).number_format = '#,##0.00'
                    row_total += amount
                ws.cell(row, len(sorted_tenders)+2, row_total).number_format = '#,##0.00'
                ws.cell(row, len(sorted_tenders)+2).font = Font(bold=True)
                service_total += row_total
                row += 1

        # Service total
        ws.cell(row, 1, f'{service_type} Total').font = Font(bold=True)
        ws.cell(row, 1).fill = total_fill
        ws.cell(row, len(sorted_tenders)+2, service_total).number_format = '#,##0.00'
        ws.cell(row, len(sorted_tenders)+2).font = Font(bold=True)
        ws.cell(row, len(sorted_tenders)+2).fill = total_fill
        row += 2

    # Adjust column widths
    ws.column_dimensions['A'].width = 25
    for col_idx in range(2, len(sorted_tenders)+3):
        ws.column_dimensions[chr(64+col_idx)].width = 15

    # Save to BytesIO
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'sales_summary_{start_date}_{end_date}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


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


# ---------------------------------------------------------------------------
# Accountabilities Routes
# ---------------------------------------------------------------------------

@bp.route("/accountabilities", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def accountabilities():
    """Main accountabilities page"""
    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    category_id = request.args.get('category_id')

    # Default to current month if no dates provided
    today = date.today()
    if not start_date_str:
        start_date = date(today.year, today.month, 1)
    else:
        start_date = date.fromisoformat(start_date_str)

    if not end_date_str:
        end_date = today
    else:
        end_date = date.fromisoformat(end_date_str)

    # Get all fund categories
    fund_categories = FundCategory.query.filter_by(active=True).order_by(FundCategory.sort_order).all()

    # Build query for funds received
    received_query = FundReceived.query.filter(
        FundReceived.record_date >= str(start_date),
        FundReceived.record_date <= str(end_date)
    )
    if category_id:
        received_query = received_query.filter_by(fund_category_id=int(category_id))
    funds_received = received_query.order_by(FundReceived.record_date.desc(), FundReceived.id.desc()).all()

    # Build query for funds disbursed
    disbursed_query = FundDisbursed.query.filter(
        FundDisbursed.record_date >= str(start_date),
        FundDisbursed.record_date <= str(end_date)
    )
    if category_id:
        disbursed_query = disbursed_query.filter_by(fund_category_id=int(category_id))
    funds_disbursed = disbursed_query.order_by(FundDisbursed.record_date.desc(), FundDisbursed.id.desc()).all()

    # Calculate totals
    total_received = sum(f.amount for f in funds_received if f.status == 'posted')
    total_disbursed = sum(f.amount for f in funds_disbursed if f.status == 'posted')

    context = {
        'fund_categories': fund_categories,
        'funds_received': funds_received,
        'funds_disbursed': funds_disbursed,
        'total_received': total_received,
        'total_disbursed': total_disbursed,
        'start_date': start_date,
        'end_date': end_date,
        'selected_category_id': int(category_id) if category_id else None,
        'app_label': app_label,
    }
    return render_template("daily_sales/accountabilities.html", **context)


@bp.route("/fund_received/new", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_fund_received():
    """Create new fund received record"""
    if request.method == "POST":
        try:
            fund_category_id = request.form.get('fund_category_id')
            amount = float(request.form.get('amount', 0))
            record_date = request.form.get('record_date')
            reference_number = request.form.get('reference_number', '').strip()
            description = request.form.get('description', '').strip()

            if not fund_category_id or not record_date or amount <= 0:
                flash("Please provide category, date, and valid amount", "danger")
                return redirect(url_for('daily_sales.accountabilities'))

            fund_received = FundReceived(
                fund_category_id=int(fund_category_id),
                amount=amount,
                record_date=record_date,
                reference_number=reference_number,
                description=description,
                status='posted',  # Auto-post for simplicity
                created_by_id=current_user.id,
                submitted_by_id=current_user.id,
                submitted_at=datetime.utcnow(),
                approved_by_id=current_user.id,
                approved_at=datetime.utcnow(),
            )

            db.session.add(fund_received)
            db.session.commit()

            flash("Fund received record created successfully", "success")
            return redirect(url_for('daily_sales.accountabilities'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating fund received: {str(e)}", "danger")
            return redirect(url_for('daily_sales.accountabilities'))

    # GET request - redirect to main page
    return redirect(url_for('daily_sales.accountabilities'))


@bp.route("/fund_disbursed/new", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_fund_disbursed():
    """Create new fund disbursed record"""
    if request.method == "POST":
        try:
            fund_category_id = request.form.get('fund_category_id')
            amount = float(request.form.get('amount', 0))
            record_date = request.form.get('record_date')
            reference_number = request.form.get('reference_number', '').strip()
            description = request.form.get('description', '').strip()

            if not fund_category_id or not record_date or amount <= 0:
                flash("Please provide category, date, and valid amount", "danger")
                return redirect(url_for('daily_sales.accountabilities'))

            fund_disbursed = FundDisbursed(
                fund_category_id=int(fund_category_id),
                amount=amount,
                record_date=record_date,
                reference_number=reference_number,
                description=description,
                status='posted',  # Auto-post for simplicity
                created_by_id=current_user.id,
                submitted_by_id=current_user.id,
                submitted_at=datetime.utcnow(),
                approved_by_id=current_user.id,
                approved_at=datetime.utcnow(),
            )

            db.session.add(fund_disbursed)
            db.session.commit()

            flash("Fund disbursed record created successfully", "success")
            return redirect(url_for('daily_sales.accountabilities'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating fund disbursed: {str(e)}", "danger")
            return redirect(url_for('daily_sales.accountabilities'))

    # GET request - redirect to main page
    return redirect(url_for('daily_sales.accountabilities'))


@bp.route("/fund_received/<int:id>/cancel", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel_fund_received(id):
    """Cancel fund received record (soft delete)"""
    fund = FundReceived.query.get_or_404(id)

    if fund.status == 'cancelled':
        flash("Record is already cancelled", "warning")
        return redirect(url_for('daily_sales.accountabilities'))

    try:
        reason = request.form.get('reason', '').strip()

        fund.status = 'cancelled'
        fund.cancelled_by_id = current_user.id
        fund.cancelled_at = datetime.now()
        fund.cancellation_reason = reason if reason else 'Cancelled by user'

        db.session.commit()
        flash("Fund received record cancelled successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling record: {str(e)}", "danger")
    return redirect(url_for('daily_sales.accountabilities'))


@bp.route("/fund_disbursed/<int:id>/cancel", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel_fund_disbursed(id):
    """Cancel fund disbursed record (soft delete)"""
    fund = FundDisbursed.query.get_or_404(id)

    if fund.status == 'cancelled':
        flash("Record is already cancelled", "warning")
        return redirect(url_for('daily_sales.accountabilities'))

    try:
        reason = request.form.get('reason', '').strip()

        fund.status = 'cancelled'
        fund.cancelled_by_id = current_user.id
        fund.cancelled_at = datetime.now()
        fund.cancellation_reason = reason if reason else 'Cancelled by user'

        db.session.commit()
        flash("Fund disbursed record cancelled successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error cancelling record: {str(e)}", "danger")
    return redirect(url_for('daily_sales.accountabilities'))


# ---------------------------------------------------------------------------
# Petty Cash Management Routes
# ---------------------------------------------------------------------------

@bp.route("/petty_cash_management", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def petty_cash_management():
    """Petty Cash Management page"""
    from application.extensions import next_control_number

    # Get filter parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    today = ph_today()
    if not start_date_str:
        start_date = date(today.year, today.month, 1)
    else:
        start_date = date.fromisoformat(start_date_str)

    if not end_date_str:
        end_date = today
    else:
        end_date = date.fromisoformat(end_date_str)

    # Get vouchers within date range
    vouchers = PettyCashVoucher.query.filter(
        PettyCashVoucher.record_date >= str(start_date),
        PettyCashVoucher.record_date <= str(end_date)
    ).order_by(PettyCashVoucher.record_date.desc(), PettyCashVoucher.id.desc()).all()

    # Get reimbursement reports
    reports = ReimbursementReport.query.order_by(
        ReimbursementReport.created_date.desc()
    ).all()

    # Get pending reports (for reimbursement linking)
    pending_reports = ReimbursementReport.query.filter_by(status='pending').all()

    # Generate next numbers
    next_pcv = next_control_number(PettyCashVoucher, 'pcv_number') if PettyCashVoucher.query.count() > 0 else "PCV-0001"
    next_ref = next_control_number(ReimbursementReceived, 'reference_number') if ReimbursementReceived.query.count() > 0 else "REF-0001"

    # Get all payees for autocomplete
    payees = Payee.query.filter_by(active=True).order_by(Payee.name).all()

    # Get all bank accounts for autocomplete
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.account_name).all()

    context = {
        'app_label': app_label,
        'vouchers': vouchers,
        'reports': reports,
        'pending_reports': pending_reports,
        'next_pcv': next_pcv,
        'next_ref': next_ref,
        'payees': payees,
        'bank_accounts': bank_accounts,
        'start_date': str(start_date),
        'end_date': str(end_date),
        'today': str(today),
    }
    return render_template("daily_sales/petty_cash_management.html", **context)


@bp.route("/petty_cash/voucher/new", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_petty_cash_voucher():
    """Create new petty cash voucher"""
    from application.extensions import next_control_number

    try:
        record_date = request.form.get('date')
        payee_name = request.form.get('payee', '').strip()
        amount = float(request.form.get('amount', 0))
        description = request.form.get('description', '').strip()

        if not record_date or not payee_name or amount <= 0:
            flash("Please provide date, payee, and valid amount", "danger")
            return redirect(url_for('daily_sales.petty_cash_management'))

        # Get or create payee
        payee = Payee.query.filter_by(name=payee_name).first()
        if not payee:
            payee = Payee(name=payee_name, active=True)
            db.session.add(payee)
            db.session.flush()

        # Generate PCV number
        pcv_number = next_control_number(PettyCashVoucher, 'pcv_number') if PettyCashVoucher.query.count() > 0 else "PCV-0001"

        # Create voucher
        voucher = PettyCashVoucher(
            pcv_number=pcv_number,
            record_date=record_date,
            payee_id=payee.id,
            amount=amount,
            description=description,
            status='draft',
            created_by_id=current_user.id
        )

        db.session.add(voucher)
        db.session.commit()

        flash(f'Petty Cash Voucher {pcv_number} created successfully!', 'success')
        return redirect(url_for('daily_sales.petty_cash_management'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating voucher: {str(e)}', 'danger')
        return redirect(url_for('daily_sales.petty_cash_management'))


@bp.route("/petty_cash/voucher/<int:voucher_id>/submit", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def submit_petty_cash_voucher(voucher_id):
    """Submit draft voucher"""
    voucher = PettyCashVoucher.query.get_or_404(voucher_id)

    if not voucher.can_submit:
        flash('Only draft vouchers can be submitted', 'warning')
        return redirect(url_for('daily_sales.petty_cash_management'))

    voucher.status = 'submitted'
    voucher.submitted_by_id = current_user.id
    voucher.submitted_at = datetime.now()

    db.session.commit()
    flash(f'Voucher {voucher.pcv_number} submitted successfully!', 'success')
    return redirect(url_for('daily_sales.petty_cash_management'))


@bp.route("/petty_cash/voucher/<int:voucher_id>/post", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def post_petty_cash_voucher(voucher_id):
    """Post submitted voucher (admin only)"""
    if not current_user.admin and not current_user.superuser:
        flash('Only admins can post vouchers', 'danger')
        return redirect(url_for('daily_sales.petty_cash_management'))

    voucher = PettyCashVoucher.query.get_or_404(voucher_id)

    if not voucher.can_post:
        flash('Only submitted vouchers can be posted', 'warning')
        return redirect(url_for('daily_sales.petty_cash_management'))

    voucher.status = 'posted'
    voucher.posted_by_id = current_user.id
    voucher.posted_at = datetime.now()

    db.session.commit()
    flash(f'Voucher {voucher.pcv_number} posted successfully!', 'success')
    return redirect(url_for('daily_sales.petty_cash_management'))


@bp.route("/petty_cash/voucher/<int:voucher_id>/cancel", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel_petty_cash_voucher(voucher_id):
    """Cancel voucher"""
    voucher = PettyCashVoucher.query.get_or_404(voucher_id)

    if not voucher.can_cancel:
        flash('This voucher cannot be cancelled', 'warning')
        return redirect(url_for('daily_sales.petty_cash_management'))

    reason = request.form.get('reason', '').strip()

    voucher.status = 'cancelled'
    voucher.cancelled_by_id = current_user.id
    voucher.cancelled_at = datetime.now()
    voucher.cancelled_reason = reason

    db.session.commit()
    flash(f'Voucher {voucher.pcv_number} cancelled', 'info')
    return redirect(url_for('daily_sales.petty_cash_management'))


@bp.route("/petty_cash/reimbursement_report/create", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def create_reimbursement_report():
    """Create reimbursement report from selected vouchers"""
    from application.extensions import next_control_number

    try:
        voucher_ids = request.form.getlist('voucher_ids[]')

        if not voucher_ids:
            flash('No vouchers selected', 'warning')
            return redirect(url_for('daily_sales.petty_cash_management'))

        # Get selected vouchers
        vouchers = PettyCashVoucher.query.filter(
            PettyCashVoucher.id.in_(voucher_ids),
            PettyCashVoucher.status == 'posted'
        ).all()

        if not vouchers:
            flash('No valid posted vouchers found', 'warning')
            return redirect(url_for('daily_sales.petty_cash_management'))

        # Calculate period
        dates = [datetime.strptime(v.record_date, '%Y-%m-%d').date() for v in vouchers]
        period_start = str(min(dates))
        period_end = str(max(dates))

        # Generate report number
        report_number = next_control_number(ReimbursementReport, 'report_number') if ReimbursementReport.query.count() > 0 else "RPT-001"

        # Create report
        report = ReimbursementReport(
            report_number=report_number,
            created_date=str(ph_today()),
            period_start=period_start,
            period_end=period_end,
            status='pending',
            prepared_by_id=current_user.id
        )

        db.session.add(report)
        db.session.flush()

        # Link vouchers to report
        total = 0
        for voucher in vouchers:
            voucher.status = 'for_reimbursement'
            voucher.reimbursement_report_id = report.id
            total += voucher.amount

        report.total_amount = total

        db.session.commit()
        flash(f'Reimbursement Report {report_number} created with {len(vouchers)} vouchers (₱{total:,.2f})', 'success')
        return redirect(url_for('daily_sales.petty_cash_management'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error creating report: {str(e)}', 'danger')
        return redirect(url_for('daily_sales.petty_cash_management'))


@bp.route("/petty_cash/reimbursement/new", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_reimbursement_received():
    """Record reimbursement received"""
    from application.extensions import next_control_number

    try:
        record_date = request.form.get('date')
        bank_account_name = request.form.get('bank_account', '').strip()
        amount = float(request.form.get('amount', 0))
        notes = request.form.get('notes', '').strip()
        report_ids = request.form.getlist('report_ids[]')

        if not record_date or not bank_account_name or amount <= 0:
            flash("Please provide date, bank account, and valid amount", "danger")
            return redirect(url_for('daily_sales.petty_cash_management'))

        # Get bank account
        bank_account = BankAccount.query.filter_by(account_name=bank_account_name).first()
        if not bank_account:
            flash("Bank account not found", "danger")
            return redirect(url_for('daily_sales.petty_cash_management'))

        # Generate reference number
        ref_number = next_control_number(ReimbursementReceived, 'reference_number') if ReimbursementReceived.query.count() > 0 else "REF-0001"

        # Create reimbursement received record
        reimbursement = ReimbursementReceived(
            reference_number=ref_number,
            record_date=record_date,
            bank_account_id=bank_account.id,
            amount=amount,
            notes=notes,
            created_by_id=current_user.id
        )

        db.session.add(reimbursement)
        db.session.flush()

        # Update linked reports status to reimbursed
        if report_ids:
            reports = ReimbursementReport.query.filter(ReimbursementReport.id.in_(report_ids)).all()
            for report in reports:
                report.status = 'reimbursed'
                # Update vouchers under this report
                for voucher in report.vouchers:
                    voucher.status = 'reimbursed'

        db.session.commit()
        flash(f'Reimbursement {ref_number} recorded successfully!', 'success')
        return redirect(url_for('daily_sales.petty_cash_management'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error recording reimbursement: {str(e)}', 'danger')
        return redirect(url_for('daily_sales.petty_cash_management'))


@bp.route("/petty_cash/payees", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def get_payees():
    """API endpoint for payee autocomplete"""
    payees = Payee.query.filter_by(active=True).order_by(Payee.name).all()
    return {'payees': [p.name for p in payees]}


@bp.route("/petty_cash/payee/add", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def add_payee():
    """Add new payee"""
    name = request.form.get('name', '').strip()

    if not name:
        return {'success': False, 'message': 'Payee name is required'}

    # Check if exists
    existing = Payee.query.filter_by(name=name).first()
    if existing:
        return {'success': False, 'message': 'Payee already exists'}

    payee = Payee(name=name, active=True)
    db.session.add(payee)
    db.session.commit()

    return {'success': True, 'payee': name}


# ---------------------------------------------------------------------------
# Change Request Routes
# ---------------------------------------------------------------------------

from .change_request_views import (
    request_transaction_change,
    request_transaction_cancellation,
    change_requests_list,
    review_change_request,
    change_history,
    transaction_history
)

bp.route('/transaction/<int:transaction_id>/request_change', methods=['GET', 'POST'])(
    login_required(roles_accepted([ROLES_ACCEPTED])(request_transaction_change))
)

bp.route('/transaction/<int:transaction_id>/request_cancellation', methods=['GET', 'POST'])(
    login_required(roles_accepted([ROLES_ACCEPTED])(request_transaction_cancellation))
)

bp.route('/change_requests', methods=['GET'])(
    login_required(roles_accepted([ROLES_ACCEPTED])(change_requests_list))
)

bp.route('/change_request/<int:request_id>/review', methods=['POST'])(
    login_required(roles_accepted([ROLES_ACCEPTED])(review_change_request))
)

bp.route('/change_history', methods=['GET'])(
    login_required(roles_accepted([ROLES_ACCEPTED])(change_history))
)

bp.route('/transaction/<int:transaction_id>/history', methods=['GET'])(
    login_required(roles_accepted([ROLES_ACCEPTED])(transaction_history))
)

