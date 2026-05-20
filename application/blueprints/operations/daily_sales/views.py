from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from datetime import date, datetime
from sqlalchemy import func

from ...user import login_required, roles_accepted, current_user
from ...register.customer import Customer
from application.extensions import db
from ..bank_account.models import BankAccount

from . import app_label, app_name
from .models import Transaction, TransactionDetail, TransactionTender, TransactionType, Deposit, DepositItem
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
    from datetime import timedelta

    today = date.today()
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
    type_id = request.args.get('type_id', type=int)
    transaction_type = TransactionType.query.get(type_id) if type_id else TransactionType.query.order_by(TransactionType.sort_order).first()
    form = Form()
    form.user_prepare_id = current_user.id
    form.record_date = str(date.today())  # default to today
    form.record_number = _generate_record_number()
    form.transaction_type_id = transaction_type.id if transaction_type else None

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
        self.report_date: date = date.today()
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

