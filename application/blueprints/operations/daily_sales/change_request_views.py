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
    """Create a snapshot of transaction data for change tracking"""
    return {
        'record_date': transaction.record_date,
        'dashlabs_number': transaction.dashlabs_number or '',
        'pos_number': transaction.pos_number or '',
        'customer_id': transaction.customer_id,
        'customer_name': transaction.customer.customer_name if transaction.customer else '',
        'description': transaction.description or '',
        'discount': float(transaction.discount) if transaction.discount else 0.0,
    }


def request_transaction_change(transaction_id):
    """
    Staff/Supervisor creates a change request for a posted transaction.

    GET: Show form with current transaction values
    POST: Create change request with old/new values
    """
    user = get_current_user()

    if not can_request_changes(user):
        flash('You do not have permission to request changes.', 'danger')
        return redirect(url_for('daily_sales.home'))

    transaction = Transaction.query.get_or_404(transaction_id)

    # Can only request changes on submitted or posted transactions
    if not (transaction.is_submitted or transaction.is_posted):
        flash('Can only request changes on submitted or posted transactions.', 'warning')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the change request.', 'warning')
            return render_template(
                'daily_sales/request_change.html',
                transaction=transaction
            )

        # Create change request
        change_request = ChangeRequest(
            transaction_id=transaction.id,
            reason=reason,
            status='pending',
            requested_by_id=user.id,
            requested_at=datetime.utcnow()
        )

        # Capture old and new values
        change_request.old_values = _snapshot_transaction(transaction)
        change_request.new_values = {
            'record_date': request.form.get('record_date', transaction.record_date),
            'dashlabs_number': request.form.get('dashlabs_number', transaction.dashlabs_number or ''),
            'pos_number': request.form.get('pos_number', transaction.pos_number or ''),
            'customer_id': int(request.form.get('customer_id', transaction.customer_id)),
            'customer_name': request.form.get('customer_name', ''),
            'description': request.form.get('description', transaction.description or ''),
            'discount': float(request.form.get('discount', transaction.discount or 0)),
        }

        db.session.add(change_request)
        db.session.commit()

        flash('Change request submitted. An admin will review it.', 'success')
        return redirect(url_for('daily_sales.view_transaction', transaction_id=transaction_id))

    return render_template(
        'daily_sales/request_change.html',
        transaction=transaction
    )


def change_requests_list():
    """
    Admin/SuperUser views pending change requests and submitted records.
    """
    # Get pending change requests (modifications and cancellations)
    pending_requests = ChangeRequest.query.filter_by(status='pending') \
        .order_by(ChangeRequest.requested_at.desc()).all()

    # Get submitted transactions waiting for approval (using new status field)
    submitted_transactions = Transaction.query.filter_by(
        status='submitted'
    ).order_by(Transaction.submitted_at.desc()).all()

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
    """
    user = get_current_user()
    change_request = ChangeRequest.query.get_or_404(request_id)

    action = request.form.get('action')  # approve | reject
    review_notes = request.form.get('review_notes', '').strip()

    if action == 'approve':
        # Handle cancellation requests differently
        if change_request.is_cancellation:
            record = change_request.record

            if record:
                # Cancel the record
                record.cancelled = datetime.utcnow()
                record.cancelled_by_id = user.id
                record.cancellation_reason = change_request.reason

                change_request.status = 'approved'
                flash('Cancellation request approved. Record has been cancelled.', 'success')
            else:
                flash('Record not found for cancellation.', 'danger')
                return redirect(url_for('daily_sales.change_requests_list'))
        else:
            # Handle modification requests
            transaction = Transaction.query.get(change_request.transaction_id)

            if transaction:
                new_vals = change_request.new_values

                # Apply changes
                transaction.record_date = new_vals.get('record_date', transaction.record_date)
                transaction.dashlabs_number = new_vals.get('dashlabs_number', transaction.dashlabs_number)
                transaction.pos_number = new_vals.get('pos_number', transaction.pos_number)
                transaction.customer_id = new_vals.get('customer_id', transaction.customer_id)
                transaction.description = new_vals.get('description', transaction.description)
                transaction.discount = new_vals.get('discount', transaction.discount)
                transaction.updated_at = datetime.utcnow()

                # Mark transaction as needing re-approval (back to submitted)
                transaction.status = 'submitted'
                transaction.submitted_by_id = user.id
                transaction.submitted_at = datetime.utcnow()

            change_request.status = 'approved'
            flash('Change request approved. Transaction requires re-approval.', 'success')

    elif action == 'reject':
        change_request.status = 'rejected'
        flash('Change request rejected.', 'warning')

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
