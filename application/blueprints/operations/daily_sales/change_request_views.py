"""
Change Request Views for Transaction Modifications

This module handles the workflow for staff requesting changes to posted transactions.
"""
from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime

from application.extensions import db
from application.blueprints.user.models import User
from .models import Transaction, TransactionDetail, TransactionTender
from .change_request_models import ChangeRequest
from .permissions import (
    get_current_user,
    can_request_changes,
    can_approve_change_requests,
    admin_required
)


def _snapshot_transaction(transaction):
    """
    Create a comprehensive snapshot of transaction data for change tracking.
    Includes header fields, line items (products), and tenders (payment).
    """
    # Basic transaction fields
    snapshot = {
        'record_date': transaction.record_date,
        'record_number': transaction.record_number or '',
        'dashlabs_number': transaction.dashlabs_number or '',
        'pos_number': transaction.pos_number or '',
        'customer_id': transaction.customer_id,
        'customer_name': str(transaction.customer) if transaction.customer else '',
        'transaction_type_id': transaction.transaction_type_id,
        'transaction_type_name': transaction.transaction_type.type_name if transaction.transaction_type else '',
        'ape_batch_id': transaction.ape_batch_id,
        'description': transaction.description or '',
        'discount': float(transaction.discount) if transaction.discount else 0.0,
    }

    # Line items (products/services)
    details = []
    for detail in transaction.transaction_details:
        details.append({
            'id': detail.id,
            'product_id': detail.product_id,
            'product_name': detail.product.product_name if detail.product else '',
            'amount': float(detail.amount) if detail.amount else 0.0,
            'discount': float(detail.discount) if detail.discount else 0.0,
            'side_note': detail.side_note or '',
        })
    snapshot['details'] = details

    # Tenders (payment methods)
    tenders = []
    for tender in transaction.transaction_tenders:
        tenders.append({
            'id': tender.id,
            'tender_id': tender.tender_id,
            'tender_name': tender.tender.tender_name if tender.tender else '',
            'amount': float(tender.amount) if tender.amount else 0.0,
            'side_note': tender.side_note or '',
        })
    snapshot['tenders'] = tenders

    # Calculate totals for reference
    items_total = sum(d['amount'] - d['discount'] for d in details)
    grand_total = items_total - snapshot['discount']
    payment_total = sum(t['amount'] for t in tenders)

    snapshot['items_total'] = items_total
    snapshot['grand_total'] = grand_total
    snapshot['payment_total'] = payment_total

    return snapshot


def request_transaction_change(transaction_id):
    """
    Staff/Supervisor creates a change request for a submitted/approved transaction.

    GET: Show form with current transaction values
    POST: Create change request with old/new values (including line items)
    """
    import sys
    user = get_current_user()

    # Comprehensive debug logging
    print("=" * 80, file=sys.stderr)
    print(f"DEBUG: request_transaction_change called for transaction_id={transaction_id}", file=sys.stderr)
    print(f"DEBUG: session.get('user_id')={session.get('user_id')}", file=sys.stderr)
    print(f"DEBUG: user={user}", file=sys.stderr)
    if user:
        print(f"DEBUG: user.user_name={user.user_name}", file=sys.stderr)
        print(f"DEBUG: user.staff (column)={user.staff}", file=sys.stderr)
        print(f"DEBUG: hasattr(user, 'is_staff')={hasattr(user, 'is_staff')}", file=sys.stderr)
        try:
            is_staff_value = user.is_staff
            print(f"DEBUG: user.is_staff (property)={is_staff_value}", file=sys.stderr)
        except Exception as e:
            print(f"DEBUG: ERROR accessing user.is_staff: {e}", file=sys.stderr)
        print(f"DEBUG: can_request_changes(user)={can_request_changes(user)}", file=sys.stderr)
    else:
        print("DEBUG: user is None!", file=sys.stderr)
    print("=" * 80, file=sys.stderr)
    sys.stderr.flush()

    if not can_request_changes(user):
        flash('You do not have permission to request changes.', 'danger')
        return redirect(url_for('daily_sales.home'))

    transaction = Transaction.query.get_or_404(transaction_id)

    # Can only request changes on submitted or approved transactions
    if not transaction.submitted:
        flash('Can only request changes on submitted or approved transactions.', 'warning')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    if transaction.cancelled:
        flash('Cannot request changes on cancelled transactions.', 'warning')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    # Check if there's already a pending modification request
    from ...register.customer import Customer
    from ...register.product import Product
    from ...register.tender import Tender

    existing_request = ChangeRequest.query.filter_by(
        record_type='transaction',
        record_id=transaction.id,
        request_action='modification',
        status='pending'
    ).first()

    if existing_request:
        flash('There is already a pending modification request for this transaction.', 'warning')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the change request.', 'warning')
            # Re-render form with available data
            customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
            products = Product.query.order_by(Product.product_name).all()
            tenders = Tender.query.order_by(Tender.tender_name).all()
            return render_template(
                'daily_sales/request_change.html',
                transaction=transaction,
                customers=customers,
                products=products,
                tenders=tenders
            )

        # Create change request
        change_request = ChangeRequest(
            record_type='transaction',
            record_id=transaction.id,
            transaction_id=transaction.id,  # For backwards compatibility
            request_action='modification',
            reason=reason,
            status='pending',
            requested_by_id=user.id,
            requested_at=datetime.utcnow()
        )

        # Capture current state (old values)
        change_request.old_values = _snapshot_transaction(transaction)

        # Capture proposed changes (new values)
        new_snapshot = {
            'record_date': request.form.get('record_date', transaction.record_date),
            'record_number': transaction.record_number or '',
            'dashlabs_number': request.form.get('dashlabs_number', transaction.dashlabs_number or ''),
            'pos_number': request.form.get('pos_number', transaction.pos_number or ''),
            'customer_id': int(request.form.get('customer_id', transaction.customer_id)),
            'customer_name': request.form.get('customer_name', ''),
            'transaction_type_id': transaction.transaction_type_id,
            'transaction_type_name': transaction.transaction_type.type_name if transaction.transaction_type else '',
            'ape_batch_id': transaction.ape_batch_id,
            'description': request.form.get('description', transaction.description or ''),
            'discount': float(request.form.get('discount', transaction.discount or 0)),
        }

        # Parse proposed line items (products)
        details = []
        product_ids = request.form.getlist('product_id[]')
        amounts = request.form.getlist('amount[]')
        detail_discounts = request.form.getlist('detail_discount[]')
        side_notes = request.form.getlist('side_note[]')

        for i in range(len(product_ids)):
            prod_id = int(product_ids[i]) if product_ids[i] else 0
            if prod_id:  # Only include if product selected
                product = Product.query.get(prod_id)
                details.append({
                    'product_id': prod_id,
                    'product_name': product.product_name if product else '',
                    'amount': float(amounts[i]) if i < len(amounts) and amounts[i] else 0.0,
                    'discount': float(detail_discounts[i]) if i < len(detail_discounts) and detail_discounts[i] else 0.0,
                    'side_note': side_notes[i] if i < len(side_notes) else '',
                })
        new_snapshot['details'] = details

        # Parse proposed tenders (payment)
        tenders = []
        tender_ids = request.form.getlist('tender_id[]')
        tender_amounts = request.form.getlist('tender_amount[]')
        tender_notes = request.form.getlist('tender_note[]')

        for i in range(len(tender_ids)):
            tnd_id = int(tender_ids[i]) if tender_ids[i] else 0
            if tnd_id:  # Only include if tender selected
                tender = Tender.query.get(tnd_id)
                tenders.append({
                    'tender_id': tnd_id,
                    'tender_name': tender.tender_name if tender else '',
                    'amount': float(tender_amounts[i]) if i < len(tender_amounts) and tender_amounts[i] else 0.0,
                    'side_note': tender_notes[i] if i < len(tender_notes) else '',
                })
        new_snapshot['tenders'] = tenders

        # Calculate totals
        items_total = sum(d['amount'] - d['discount'] for d in details)
        grand_total = items_total - new_snapshot['discount']
        payment_total = sum(t['amount'] for t in tenders)

        new_snapshot['items_total'] = items_total
        new_snapshot['grand_total'] = grand_total
        new_snapshot['payment_total'] = payment_total

        change_request.new_values = new_snapshot

        db.session.add(change_request)
        db.session.commit()

        flash('Modification request submitted. An admin will review it.', 'success')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    # GET: Show form
    customers = Customer.query.order_by(Customer.last_name, Customer.first_name).all()
    products = Product.query.order_by(Product.product_name).all()
    tenders = Tender.query.order_by(Tender.tender_name).all()

    return render_template(
        'daily_sales/request_change.html',
        transaction=transaction,
        customers=customers,
        products=products,
        tenders=tenders
    )


def change_requests_list():
    """
    Admin/SuperUser views pending change requests and submitted records.
    """
    from sqlalchemy import select as sa_select
    from .admin_models import AdminTransaction

    # Get pending change requests (modifications and cancellations)
    pending_requests = ChangeRequest.query.filter_by(status='pending') \
        .order_by(ChangeRequest.requested_at.desc()).all()

    # Get submitted transactions waiting for approval (using legacy workflow)
    # Submitted but not yet approved (no AdminTransaction record)
    approved_ids_select = sa_select(AdminTransaction.transaction_id)
    submitted_transactions = Transaction.query.filter(
        Transaction.submitted != None,
        Transaction.submitted != '',
        Transaction.cancelled == None,
        Transaction.id.notin_(approved_ids_select)
    ).order_by(Transaction.submitted.desc()).all()

    # Get submitted deposits waiting for approval
    from .models import Deposit
    submitted_deposits = Deposit.query.filter_by(
        status='submitted'
    ).order_by(Deposit.submitted_at.desc()).all()

    # Get submitted collections waiting for approval
    from ..collections.models import Collection
    submitted_collections = Collection.query.filter_by(
        status='submitted'
    ).order_by(Collection.submitted_at.desc()).all()

    return render_template(
        'daily_sales/change_requests.html',
        pending_requests=pending_requests,
        submitted_transactions=submitted_transactions,
        submitted_deposits=submitted_deposits,
        submitted_collections=submitted_collections
    )


def review_change_request(request_id):
    """
    Admin/SuperUser approves or rejects a change request.

    POST with action=approve or action=reject

    If approved:
    - Modification request: Apply proposed changes directly to the transaction
    - Cancellation request: Cancel the record

    If rejected:
    - No changes made to the record
    """
    user = get_current_user()
    change_request = ChangeRequest.query.get_or_404(request_id)

    action = request.form.get('action')  # approve | reject
    review_notes = request.form.get('review_notes', '').strip()

    if action == 'approve':
        # Handle cancellation requests
        if change_request.is_cancellation:
            record = change_request.record

            if record:
                # Cancel the record
                if hasattr(record, 'cancelled'):
                    from application.extensions import ph_today
                    record.cancelled = str(ph_today())
                    record.cancellation_reason = change_request.reason

                change_request.status = 'approved'

                # Audit logging
                from .audit_logger import log_status_change
                log_status_change('transaction', record, 'cancellation_approved',
                                reason=change_request.reason, notes=review_notes)

                flash('Cancellation request approved. Record has been cancelled.', 'success')
            else:
                flash('Record not found for cancellation.', 'danger')
                return redirect(url_for('daily_sales.change_requests_list'))
        else:
            # Handle modification requests - apply proposed changes
            transaction = Transaction.query.get(change_request.transaction_id)

            if transaction:
                from .audit_logger import get_model_snapshot, log_update

                # Capture current state before applying changes
                old_snapshot = get_model_snapshot(transaction)

                new_vals = change_request.new_values

                # Apply header changes
                transaction.record_date = new_vals.get('record_date', transaction.record_date)
                transaction.dashlabs_number = new_vals.get('dashlabs_number', transaction.dashlabs_number)
                transaction.pos_number = new_vals.get('pos_number', transaction.pos_number)
                transaction.customer_id = new_vals.get('customer_id', transaction.customer_id)
                transaction.description = new_vals.get('description', transaction.description)
                transaction.discount = new_vals.get('discount', transaction.discount)
                transaction.updated_at = datetime.utcnow()

                # Apply line item changes (products)
                # Delete existing details and recreate from proposed changes
                TransactionDetail.query.filter_by(transaction_id=transaction.id).delete()

                for detail_data in new_vals.get('details', []):
                    new_detail = TransactionDetail(
                        transaction_id=transaction.id,
                        product_id=detail_data['product_id'],
                        amount=detail_data['amount'],
                        discount=detail_data.get('discount', 0.0),
                        side_note=detail_data.get('side_note', '')
                    )
                    db.session.add(new_detail)

                # Apply tender changes (payment)
                # Delete existing tenders and recreate from proposed changes
                TransactionTender.query.filter_by(transaction_id=transaction.id).delete()

                for tender_data in new_vals.get('tenders', []):
                    new_tender = TransactionTender(
                        transaction_id=transaction.id,
                        tender_id=tender_data['tender_id'],
                        amount=tender_data['amount'],
                        side_note=tender_data.get('side_note', '')
                    )
                    db.session.add(new_tender)

                # Transaction remains approved (no need to re-approve)
                # Just record the modification in audit trail

                change_request.status = 'approved'

                # Audit logging
                log_update('transaction', transaction, old_snapshot,
                          reason=f"Modification request #{request_id} approved",
                          notes=f"Requested by: {change_request.requested_by.username}. Reason: {change_request.reason}. Admin note: {review_notes}")

                flash('Modification request approved. Changes have been applied.', 'success')
            else:
                flash('Transaction not found.', 'danger')
                return redirect(url_for('daily_sales.change_requests_list'))

    elif action == 'reject':
        change_request.status = 'rejected'
        flash('Change request rejected. No changes made to the transaction.', 'warning')

    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for('daily_sales.change_requests_list'))

    # Update change request review info
    change_request.reviewed_by_id = user.id
    change_request.reviewed_at = datetime.utcnow()
    change_request.review_notes = review_notes

    db.session.commit()

    return redirect(url_for('daily_sales.change_requests_list'))


def change_history():
    """
    Admin/SuperUser views history of all change requests.
    """
    history = ChangeRequest.query \
        .filter(ChangeRequest.status != 'pending') \
        .order_by(ChangeRequest.requested_at.desc()).all()

    return render_template(
        'daily_sales/change_history.html',
        history=history
    )


def transaction_history(transaction_id):
    """
    View change request history for a specific transaction.
    """
    transaction = Transaction.query.get_or_404(transaction_id)

    change_log = ChangeRequest.query.filter_by(transaction_id=transaction_id) \
        .order_by(ChangeRequest.requested_at.asc()).all()

    return render_template(
        'daily_sales/transaction_history.html',
        transaction=transaction,
        change_log=change_log
    )


def request_transaction_cancellation(transaction_id):
    """
    Staff/Supervisor requests cancellation of a posted transaction.

    GET: Show form with transaction details and reason input
    POST: Create cancellation request
    """
    user = get_current_user()

    if not can_request_changes(user):
        flash('You do not have permission to request cancellations.', 'danger')
        return redirect(url_for('daily_sales.home'))

    transaction = Transaction.query.get_or_404(transaction_id)

    # Can only request cancellation on posted transactions
    if not transaction.is_posted:
        flash('Can only request cancellation on posted transactions.', 'warning')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    # Check if there's already a pending cancellation request
    existing_request = ChangeRequest.query.filter_by(
        record_type='transaction',
        record_id=transaction.id,
        request_action='cancellation',
        status='pending'
    ).first()

    if existing_request:
        flash('There is already a pending cancellation request for this transaction.', 'warning')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the cancellation request.', 'warning')
            return render_template(
                'daily_sales/request_cancellation.html',
                transaction=transaction
            )

        # Create cancellation request
        change_request = ChangeRequest(
            record_type='transaction',
            record_id=transaction.id,
            transaction_id=transaction.id,  # For backwards compatibility
            request_action='cancellation',
            reason=reason,
            status='pending',
            requested_by_id=user.id,
            requested_at=datetime.utcnow()
        )

        # No need for old/new values for cancellation
        change_request.old_values = {}
        change_request.new_values = {}

        db.session.add(change_request)
        db.session.commit()

        flash('Cancellation request submitted. An admin will review it.', 'success')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    return render_template(
        'daily_sales/request_cancellation.html',
        transaction=transaction
    )
