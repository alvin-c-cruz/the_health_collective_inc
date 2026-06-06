from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from application.blueprints.user import login_required, roles_accepted
from application.extensions import db, ph_today

from . import app_name, app_label
from .models import Collection, CollectionDetail
from ..daily_sales.models import TransactionTender, Transaction
from ..ape_batch.models import ApeBatch
from ..bank_account.models import BankAccount
from ...register.tender.models import Tender

from application.blueprints.audit.utils import (
    log_create, log_update, log_delete, log_status_change,
    model_to_dict, get_record_identifier
)

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _receivable_tenders():
    return Tender.query.filter_by(is_receivable=True).order_by(Tender.sort_order.desc()).all()


def _outstanding_lines(tender_id=None, ape_batch_id=None):
    """All TransactionTender lines for receivable tenders, with outstanding balance."""
    receivable_ids = {t.id for t in _receivable_tenders()}
    query = TransactionTender.query.filter(
        TransactionTender.tender_id.in_(receivable_ids)
    ).join(TransactionTender.transaction).filter(
        db.text("\"transaction\".submitted IS NOT NULL"),  # Include all submitted transactions
        db.text("\"transaction\".cancelled IS NULL"),
    )
    if tender_id:
        query = query.filter(TransactionTender.tender_id == tender_id)
    if ape_batch_id:
        query = query.filter(Transaction.ape_batch_id == ape_batch_id)
    return query.all()


def _collected(tt_id, exclude_collection_id=None):
    """Sum already applied to a TransactionTender line.

    Args:
        tt_id: Transaction tender ID
        exclude_collection_id: Optional collection ID to exclude (for editing)
    """
    query = db.session.query(
        db.func.coalesce(db.func.sum(CollectionDetail.amount_applied), 0)
    ).filter_by(transaction_tender_id=tt_id)

    # Exclude specific collection if specified (for edit mode)
    if exclude_collection_id:
        query = query.filter(CollectionDetail.collection_id != exclude_collection_id)

    result = query.scalar()
    return float(result)


# ---------------------------------------------------------------------------
# Receivables dashboard
# ---------------------------------------------------------------------------

@bp.route("/")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def home():
    tender_id = request.args.get("tender_id", type=int)
    tenders = _receivable_tenders()

    lines = _outstanding_lines(tender_id)
    rows = []
    for tt in lines:
        collected = _collected(tt.id)
        outstanding = tt.amount - collected
        rows.append({
            "tt": tt,
            "collected": collected,
            "outstanding": outstanding,
            "is_settled": outstanding <= 0,
        })

    show_settled = request.args.get("show_settled") == "1"
    if not show_settled:
        rows = [r for r in rows if not r["is_settled"]]

    # Group rows by tender, preserving tender sort order
    from collections import OrderedDict
    groups = OrderedDict()
    for r in rows:
        name = r["tt"].tender.tender_name if r["tt"].tender else "—"
        groups.setdefault(name, []).append(r)

    total_outstanding = sum(r["outstanding"] for r in rows if not r["is_settled"])

    context = {
        "app_label": app_label,
        "tenders": tenders,
        "selected_tender_id": tender_id,
        "groups": groups,
        "show_settled": show_settled,
        "total_outstanding": total_outstanding,
    }
    return render_template("collections/home.html", **context)


# ---------------------------------------------------------------------------
# New collection
# ---------------------------------------------------------------------------

@bp.route("/new", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def new_collection():
    tenders      = _receivable_tenders()
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()
    ape_batches  = ApeBatch.query.order_by(ApeBatch.batch_date.desc()).all()

    if request.method == "POST":
        import json
        f = request.form

        collection_date = f.get("collection_date", str(ph_today()))
        tender_id       = f.get("tender_id", type=int)
        bank_account_id = f.get("bank_account_id", type=int) or None
        ape_batch_id    = f.get("ape_batch_id", type=int) or None
        reference       = (f.get("reference") or "").strip()
        notes           = (f.get("notes") or "").strip()

        # Get deductions
        deduction_descriptions = f.getlist("deduction_description[]")
        deduction_amounts = f.getlist("deduction_amount[]")

        # Build deductions JSON
        deductions_list = []
        for desc, amt in zip(deduction_descriptions, deduction_amounts):
            try:
                amount = float(amt or 0)
                if amount > 0:  # Only include non-zero deductions
                    deductions_list.append({
                        "description": desc.strip(),
                        "amount": amount
                    })
            except (ValueError, TypeError):
                continue

        deductions_json = json.dumps(deductions_list)

        line_ids     = f.getlist("line_id")
        line_amounts = f.getlist("line_amount")

        if not tender_id:
            flash("Please select a tender.", "danger")
        elif not line_ids:
            flash("Please select at least one transaction line.", "danger")
        else:
            col = Collection(
                collection_date=collection_date,
                tender_id=tender_id,
                bank_account_id=bank_account_id,
                ape_batch_id=ape_batch_id,
                reference=reference,
                notes=notes,
                deductions=deductions_json,
                status='draft',  # New workflow: start as draft
                created_by_id=current_user.id,
                created_at=str(ph_today()),
                updated_at=datetime.now(),
                # Legacy field for backwards compatibility
                recorded_by=current_user.id,
            )
            db.session.add(col)
            db.session.flush()

            txn_list = []  # Build list for audit log
            for lid, lamt in zip(line_ids, line_amounts):
                try:
                    amt = float(lamt)
                except (ValueError, TypeError):
                    continue
                if amt <= 0:
                    continue
                detail = CollectionDetail(
                    collection_id=col.id,
                    transaction_tender_id=int(lid),
                    amount_applied=amt,
                )
                db.session.add(detail)

                # Add to audit log list
                from application.blueprints.operations.daily_sales.models import TransactionTender
                txn_tender = TransactionTender.query.get(int(lid))
                if txn_tender and txn_tender.transaction:
                    txn = txn_tender.transaction
                    txn_list.append(f"#{txn.record_number} - {txn.customer.customer_name if txn.customer else 'No customer'} (₱{amt:,.2f})")

            # Build transaction details for audit log
            txn_details = "; ".join(txn_list) if txn_list else "No transactions"

            # Log collection creation
            log_create(
                module='collection',
                record_id=col.id,
                record_identifier=f"Collection #{col.id} - {col.tender.tender_name if col.tender else 'N/A'} - ₱{col.formatted_total_amount}",
                new_values=model_to_dict(col, [
                    'collection_date', 'tender_id', 'bank_account_id', 'ape_batch_id',
                    'reference', 'notes', 'status'
                ]),
                notes=f'Draft collection created with {len(line_ids)} line items. Transactions: {txn_details}'
            )

            db.session.commit()
            flash(f"Collection saved as draft. Net amount: ₱{col.formatted_net_amount}", "success")
            # Redirect to daily_sales with the collection date
            return redirect(url_for("daily_sales.home", date=col.collection_date))

    tender_id_pre    = request.args.get("tender_id", type=int)
    ape_batch_id_pre = request.args.get("ape_batch_id", type=int)
    date_param       = request.args.get("date")  # Get date from URL parameter

    # Get Credit tender ID for APE collections
    credit_tender = Tender.query.filter(Tender.tender_name == 'Credit').first()
    credit_tender_id = credit_tender.id if credit_tender else None

    lines = _outstanding_lines(tender_id_pre, ape_batch_id_pre) if (tender_id_pre or ape_batch_id_pre) else []
    outstanding_rows = []
    for tt in lines:
        collected = _collected(tt.id)
        outstanding = tt.amount - collected
        if outstanding > 0:
            outstanding_rows.append({"tt": tt, "outstanding": outstanding})

    # Use date parameter if provided, otherwise use today
    default_date = date_param if date_param else str(ph_today())

    context = {
        "app_label": app_label,
        "tenders": tenders,
        "bank_accounts": bank_accounts,
        "ape_batches": ape_batches,
        "outstanding_rows": outstanding_rows,
        "selected_tender_id": tender_id_pre,
        "selected_ape_batch_id": ape_batch_id_pre,
        "ape_batch_id_pre": ape_batch_id_pre,
        "credit_tender_id": credit_tender_id,
        "today": default_date,
    }
    return render_template("collections/new_collection.html", **context)


# ---------------------------------------------------------------------------
# Edit collection (draft only)
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>/edit", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def edit_collection(collection_id):
    col = Collection.query.get_or_404(collection_id)

    # Only allow editing of draft collections
    if col.status != 'draft':
        flash("Only draft collections can be edited.", "danger")
        return redirect(url_for(f"{app_name}.view_collection", collection_id=col.id))

    # Check ownership (creator or admin)
    if col.created_by_id != current_user.id and not current_user.is_admin:
        flash("You don't have permission to edit this collection.", "danger")
        return redirect(url_for(f"{app_name}.view_collection", collection_id=col.id))

    tenders      = _receivable_tenders()
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()
    ape_batches  = ApeBatch.query.order_by(ApeBatch.batch_date.desc()).all()

    if request.method == "POST":
        import json
        f = request.form

        # Store old values for audit log
        old_values = model_to_dict(col, [
            'collection_date', 'tender_id', 'bank_account_id', 'ape_batch_id',
            'reference', 'notes', 'status'
        ])

        collection_date = f.get("collection_date", str(ph_today()))
        tender_id       = f.get("tender_id", type=int)
        bank_account_id = f.get("bank_account_id", type=int) or None
        ape_batch_id    = f.get("ape_batch_id", type=int) or None
        reference       = (f.get("reference") or "").strip()
        notes           = (f.get("notes") or "").strip()

        # Get deductions
        deduction_descriptions = f.getlist("deduction_description[]")
        deduction_amounts = f.getlist("deduction_amount[]")

        # Build deductions JSON
        deductions_list = []
        for desc, amt in zip(deduction_descriptions, deduction_amounts):
            try:
                amount = float(amt or 0)
                if amount > 0:  # Only include non-zero deductions
                    deductions_list.append({
                        "description": desc.strip(),
                        "amount": amount
                    })
            except (ValueError, TypeError):
                continue

        deductions_json = json.dumps(deductions_list)

        line_ids     = f.getlist("line_id")
        line_amounts = f.getlist("line_amount")

        if not tender_id:
            flash("Please select a tender.", "danger")
        elif not line_ids:
            flash("Please select at least one transaction line.", "danger")
        else:
            # Update collection fields
            col.collection_date = collection_date
            col.tender_id = tender_id
            col.bank_account_id = bank_account_id
            col.ape_batch_id = ape_batch_id
            col.reference = reference
            col.notes = notes
            col.deductions = deductions_json
            col.updated_at = datetime.now()

            # Delete existing details
            CollectionDetail.query.filter_by(collection_id=col.id).delete()

            # Add new details
            for lid, lamt in zip(line_ids, line_amounts):
                try:
                    amt = float(lamt)
                except (ValueError, TypeError):
                    continue
                if amt <= 0:
                    continue
                detail = CollectionDetail(
                    collection_id=col.id,
                    transaction_tender_id=int(lid),
                    amount_applied=amt,
                )
                db.session.add(detail)

            # Log collection update
            new_values = model_to_dict(col, [
                'collection_date', 'tender_id', 'bank_account_id', 'ape_batch_id',
                'reference', 'notes', 'status'
            ])
            log_update(
                module='collection',
                record_id=col.id,
                record_identifier=f"Collection #{col.id} - {col.tender.tender_name if col.tender else 'N/A'} - ₱{col.formatted_total_amount}",
                old_values=old_values,
                new_values=new_values,
                notes=f'Draft collection updated with {len(line_ids)} line items'
            )

            db.session.commit()
            flash(f"Collection updated. Net amount: ₱{col.formatted_net_amount}", "success")
            return redirect(url_for(f"{app_name}.view_collection", collection_id=col.id))

    # GET request - load collection data for editing
    # Get Credit tender ID for APE collections
    credit_tender = Tender.query.filter(Tender.tender_name == 'Credit').first()
    credit_tender_id = credit_tender.id if credit_tender else None

    # Load existing collection details
    existing_details = {}
    for detail in col.details:
        existing_details[detail.transaction_tender_id] = detail.amount_applied

    # Load outstanding lines plus already-collected lines from this collection
    lines = _outstanding_lines(col.tender_id, col.ape_batch_id)
    outstanding_rows = []
    for tt in lines:
        collected = _collected(tt.id, exclude_collection_id=col.id)  # Exclude current collection
        outstanding = tt.amount - collected
        if outstanding > 0 or tt.id in existing_details:  # Include if has outstanding OR already in this collection
            outstanding_rows.append({
                "tt": tt,
                "outstanding": outstanding,
                "selected": tt.id in existing_details,
                "amount_applied": existing_details.get(tt.id, outstanding)
            })

    # Parse existing deductions
    import json
    try:
        existing_deductions = json.loads(col.deductions or '[]')
    except:
        existing_deductions = []

    context = {
        "app_label": app_label,
        "tenders": tenders,
        "bank_accounts": bank_accounts,
        "ape_batches": ape_batches,
        "outstanding_rows": outstanding_rows,
        "selected_tender_id": col.tender_id,
        "selected_ape_batch_id": col.ape_batch_id,
        "ape_batch_id_pre": col.ape_batch_id,
        "credit_tender_id": credit_tender_id,
        "today": str(ph_today()),
        "collection": col,
        "existing_deductions": existing_deductions,
        "edit_mode": True,
    }
    return render_template("collections/new_collection.html", **context)


# ---------------------------------------------------------------------------
# AJAX — load outstanding lines for a tender
# ---------------------------------------------------------------------------

@bp.route("/lines")
@login_required
def get_lines():
    from flask import jsonify
    tender_id    = request.args.get("tender_id", type=int)
    ape_batch_id = request.args.get("ape_batch_id", type=int)
    if not tender_id and not ape_batch_id:
        return jsonify([])
    lines = _outstanding_lines(tender_id, ape_batch_id)
    result = []
    for tt in lines:
        collected = _collected(tt.id)
        outstanding = round(tt.amount - collected, 2)
        if outstanding <= 0:
            continue
        t = tt.transaction
        result.append({
            "id": tt.id,
            "record_date": t.record_date or "",
            "record_number": t.record_number or "",
            "customer": t.customer.customer_name if t.customer else "",
            "amount": tt.amount,
            "collected": round(collected, 2),
            "outstanding": outstanding,
        })
    return jsonify(result)


# ---------------------------------------------------------------------------
# View collection
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def view_collection(collection_id):
    col = Collection.query.get_or_404(collection_id)
    context = {
        "app_label": app_label,
        "col": col,
    }
    return render_template("collections/view_collection.html", **context)


# ---------------------------------------------------------------------------
# Collection history
# ---------------------------------------------------------------------------

@bp.route("/history")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def history():
    cols = Collection.query.order_by(Collection.id.desc()).all()
    context = {
        "app_label": app_label,
        "cols": cols,
    }
    return render_template("collections/history.html", **context)


# ---------------------------------------------------------------------------
# Delete collection
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>/delete", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def delete_collection(collection_id):
    col = Collection.query.get_or_404(collection_id)

    # Capture old values before deletion
    old_values = model_to_dict(col, [
        'collection_date', 'tender_id', 'bank_account_id', 'status',
        'reference', 'notes'
    ])
    record_id = col.id
    identifier = f"Collection #{col.id} - {col.tender.tender_name if col.tender else 'N/A'}"

    db.session.delete(col)

    # Log deletion
    log_delete(
        module='collection',
        record_id=record_id,
        record_identifier=identifier,
        old_values=old_values,
        reason='Collection deleted by user'
    )

    db.session.commit()
    flash("Collection deleted.", "warning")
    return redirect(url_for(f"{app_name}.history"))


# ---------------------------------------------------------------------------
# Submit collection (draft → submitted or posted if admin)
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>/submit", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def submit_collection(collection_id):
    """Submit a draft collection for approval"""
    col = Collection.query.get_or_404(collection_id)

    if col.status != 'draft':
        flash('Only draft collections can be submitted.', 'danger')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    # Check ownership
    if col.created_by_id != current_user.id and not current_user.is_admin:
        flash('You can only submit your own collections.', 'danger')
        return redirect(url_for(f'{app_name}.history'))

    # Submit for approval (no auto-approval even for admins)
    col.status = 'submitted'
    col.submitted_by_id = current_user.id
    col.submitted_at = datetime.now()
    col.updated_at = datetime.now()

    # Build transaction list for audit log
    txn_list = []
    for detail in col.details:
        txn_tender = detail.transaction_tender
        txn = txn_tender.transaction
        txn_list.append(f"#{txn.record_number} - {txn.customer.customer_name if txn.customer else 'No customer'} (₱{detail.formatted_amount})")

    txn_details = "; ".join(txn_list) if txn_list else "No transactions"

    # Log submission
    log_status_change(
        module='collection',
        record_id=col.id,
        record_identifier=f"Collection #{col.id} - {col.tender.tender_name if col.tender else 'No tender'}",
        action='submitted',
        old_status='draft',
        new_status='submitted',
        notes=f'Submitted for approval. Net amount: ₱{col.formatted_net_amount}. Transactions: {txn_details}'
    )

    db.session.commit()

    flash(f'Collection submitted successfully! Waiting for approval. Net amount: ₱{col.formatted_net_amount}', 'success')

    return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))


# ---------------------------------------------------------------------------
# Approve collection (submitted → posted)
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>/approve", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def approve_collection(collection_id):
    """Admin approves a submitted collection"""
    col = Collection.query.get_or_404(collection_id)

    if col.status != 'submitted':
        flash('Only submitted collections can be approved.', 'danger')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    col.status = 'posted'
    col.approved_by_id = current_user.id
    col.approved_at = datetime.now()
    col.updated_at = datetime.now()

    # Build transaction list for audit log
    txn_list = []
    for detail in col.details:
        txn_tender = detail.transaction_tender
        txn = txn_tender.transaction
        txn_list.append(f"#{txn.record_number} - {txn.customer.customer_name if txn.customer else 'No customer'} (₱{detail.formatted_amount})")

    txn_details = "; ".join(txn_list) if txn_list else "No transactions"

    # Log approval
    log_status_change(
        module='collection',
        record_id=col.id,
        record_identifier=f"Collection #{col.id} - {col.tender.tender_name if col.tender else 'No tender'}",
        action='approved',
        old_status='submitted',
        new_status='posted',
        notes=f'Approved and posted. Total: ₱{col.formatted_total_amount}. Transactions: {txn_details}'
    )

    db.session.commit()

    flash(f'Collection approved and posted! Total amount: ₱{col.formatted_total_amount}', 'success')
    return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))


@bp.route("/<int:collection_id>/reject", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def reject_collection(collection_id):
    """Reject submitted collection - send back to draft"""
    col = Collection.query.get_or_404(collection_id)

    if col.status != 'submitted':
        flash('Only submitted collections can be rejected.', 'danger')
        return redirect(url_for('daily_sales.change_requests_list'))

    col.status = 'draft'
    col.updated_at = datetime.now()

    # Log rejection
    log_status_change(
        module='collection',
        record_id=col.id,
        record_identifier=f"Collection #{col.id}",
        action='rejected',
        old_status='submitted',
        new_status='draft',
        notes='Rejected - returned to draft'
    )

    db.session.commit()

    flash(f'Collection #{col.id} rejected and sent back to draft.', 'warning')
    return redirect(url_for('daily_sales.change_requests_list'))


# ---------------------------------------------------------------------------
# Cancel collection (soft delete with reason)
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>/cancel", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def cancel_collection(collection_id):
    """Cancel a collection with a reason (soft delete)"""
    col = Collection.query.get_or_404(collection_id)

    if col.status == 'cancelled':
        flash('This collection is already cancelled.', 'warning')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a cancellation reason.', 'danger')
            return redirect(url_for(f'{app_name}.cancel_collection', collection_id=collection_id))

        old_status = col.status
        col.status = 'cancelled'
        col.cancelled_by_id = current_user.id
        col.cancelled_at = datetime.now()
        col.cancellation_reason = reason
        col.updated_at = datetime.now()

        # Log cancellation
        log_status_change(
            module='collection',
            record_id=col.id,
            record_identifier=f"Collection #{col.id}",
            action='cancelled',
            old_status=old_status,
            new_status='cancelled',
            reason=reason
        )

        db.session.commit()

        flash(f'Collection cancelled successfully. Reason: {reason}', 'info')
        return redirect(url_for(f'{app_name}.history'))

    # GET request - show cancellation form
    context = {
        'app_label': app_label,
        'col': col,
    }
    return render_template('collections/cancel_collection.html', **context)


# ---------------------------------------------------------------------------
# Change Requests for Collections
# ---------------------------------------------------------------------------

@bp.route("/<int:collection_id>/request-change", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def request_collection_change(collection_id):
    """Staff/supervisor requests change to a posted collection"""
    from ..daily_sales.change_request_models import ChangeRequest

    col = Collection.query.get_or_404(collection_id)

    # Only submitted or posted collections can have change requests
    if col.status not in ['submitted', 'posted']:
        flash('Only submitted or posted collections can have change requests.', 'danger')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    if request.method == 'POST':
        # Capture old values
        old_values = {
            'collection_date': col.collection_date,
            'tender_id': col.tender_id,
            'bank_account_id': col.bank_account_id,
            'reference': col.reference,
            'notes': col.notes,
        }

        # Capture new values from form
        new_values = {
            'collection_date': request.form.get('collection_date', ''),
            'tender_id': request.form.get('tender_id', type=int),
            'bank_account_id': request.form.get('bank_account_id', type=int) or None,
            'reference': request.form.get('reference', ''),
            'notes': request.form.get('notes', ''),
        }

        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the change request.', 'danger')
            return redirect(url_for(f'{app_name}.request_collection_change', collection_id=collection_id))

        # Create change request
        cr = ChangeRequest()
        cr.record_type = 'collection'
        cr.record_id = collection_id
        cr.old_values = old_values
        cr.new_values = new_values
        cr.reason = reason
        cr.status = 'pending'
        cr.requested_by_id = current_user.id
        cr.requested_at = datetime.now()

        db.session.add(cr)
        db.session.commit()

        flash('Change request submitted successfully. Waiting for admin approval.', 'success')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    # GET request - show form
    tenders = _receivable_tenders()
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()

    context = {
        'app_label': app_label,
        'col': col,
        'tenders': tenders,
        'bank_accounts': bank_accounts,
    }

    return render_template('collections/request_collection_change.html', **context)


@bp.route("/<int:collection_id>/request-cancellation", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def request_collection_cancellation(collection_id):
    """Staff/supervisor requests cancellation of a posted collection"""
    from ..daily_sales.change_request_models import ChangeRequest

    col = Collection.query.get_or_404(collection_id)

    # Can only request cancellation on posted collections
    if col.status != 'posted':
        flash('Can only request cancellation on posted collections.', 'warning')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    # Check if there's already a pending cancellation request
    existing_request = ChangeRequest.query.filter_by(
        record_type='collection',
        record_id=col.id,
        request_action='cancellation',
        status='pending'
    ).first()

    if existing_request:
        flash('There is already a pending cancellation request for this collection.', 'warning')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    if request.method == 'POST':
        reason = request.form.get('reason', '').strip()

        if not reason:
            flash('Please provide a reason for the cancellation request.', 'warning')
            context = {
                'app_label': app_label,
                'col': col,
            }
            return render_template('collections/request_collection_cancellation.html', **context)

        # Create cancellation request
        cr = ChangeRequest()
        cr.record_type = 'collection'
        cr.record_id = collection_id
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
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    context = {
        'app_label': app_label,
        'col': col,
    }

    return render_template('collections/request_collection_cancellation.html', **context)


@bp.route("/change-requests", methods=["GET"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def collection_change_requests():
    """Admin views pending collection change requests"""
    from ..daily_sales.change_request_models import ChangeRequest

    # Get all pending change requests for collections
    change_requests = ChangeRequest.query.filter(
        ChangeRequest.record_type == 'collection',
        ChangeRequest.status == 'pending'
    ).order_by(ChangeRequest.requested_at.desc()).all()

    context = {
        'app_label': app_label,
        'change_requests': change_requests,
    }

    return render_template('collections/collection_change_requests.html', **context)


@bp.route("/change-requests/<int:cr_id>/review", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def review_collection_change_request(cr_id):
    """Admin approves or rejects collection change request"""
    from ..daily_sales.change_request_models import ChangeRequest

    cr = ChangeRequest.query.get_or_404(cr_id)

    # Only pending requests can be reviewed
    if cr.status != 'pending':
        flash('This change request has already been reviewed.', 'warning')
        return redirect(url_for(f'{app_name}.collection_change_requests'))

    action = request.form.get('action')  # 'approve' or 'reject'
    review_notes = request.form.get('review_notes', '').strip()

    if action == 'approve':
        # Apply the changes to the collection
        col = Collection.query.get(cr.record_id)
        if col:
            nv = cr.new_values
            col.collection_date = nv.get('collection_date') or col.collection_date
            col.tender_id = nv.get('tender_id') or col.tender_id
            col.bank_account_id = nv.get('bank_account_id')
            col.reference = nv.get('reference')
            col.notes = nv.get('notes')
            col.updated_at = datetime.now()

            # Set collection back to submitted status for re-approval
            col.status = 'submitted'
            col.submitted_by_id = current_user.id
            col.submitted_at = datetime.now()

        cr.status = 'approved'
        flash('Change request approved. Collection updated and set to submitted status for re-approval.', 'success')

    elif action == 'reject':
        cr.status = 'rejected'
        flash('Change request rejected.', 'info')

    else:
        flash('Invalid action.', 'danger')
        return redirect(url_for(f'{app_name}.collection_change_requests'))

    # Record review details
    cr.reviewed_by_id = current_user.id
    cr.reviewed_at = datetime.now()
    cr.review_notes = review_notes

    db.session.commit()

    return redirect(url_for(f'{app_name}.collection_change_requests'))


