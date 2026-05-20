from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from application.blueprints.user import login_required, roles_accepted
from application.extensions import db

from . import app_name, app_label
from .models import Collection, CollectionDetail
from ..daily_sales.models import TransactionTender
from ..bank_account.models import BankAccount
from ...register.tender.models import Tender

bp = Blueprint(app_name, __name__, template_folder="pages", url_prefix=f"/{app_name}")
ROLES_ACCEPTED = app_label


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _receivable_tenders():
    return Tender.query.filter_by(is_receivable=True).order_by(Tender.sort_order.desc()).all()


def _outstanding_lines(tender_id=None):
    """All TransactionTender lines for receivable tenders, with outstanding balance."""
    receivable_ids = {t.id for t in _receivable_tenders()}
    query = TransactionTender.query.filter(
        TransactionTender.tender_id.in_(receivable_ids)
    ).join(TransactionTender.transaction).filter(
        db.text("\"transaction\".submitted IS NOT NULL"),
        db.text("\"transaction\".cancelled IS NULL"),
    )
    if tender_id:
        query = query.filter(TransactionTender.tender_id == tender_id)
    return query.all()


def _collected(tt_id):
    """Sum already applied to a TransactionTender line."""
    result = db.session.query(
        db.func.coalesce(db.func.sum(CollectionDetail.amount_applied), 0)
    ).filter_by(transaction_tender_id=tt_id).scalar()
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
    tenders = _receivable_tenders()
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()

    if request.method == "POST":
        f = request.form

        collection_date = f.get("collection_date", str(date.today()))
        tender_id       = f.get("tender_id", type=int)
        bank_account_id = f.get("bank_account_id", type=int) or None
        reference       = (f.get("reference") or "").strip()
        notes           = (f.get("notes") or "").strip()

        line_ids    = f.getlist("line_id")
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
                reference=reference,
                notes=notes,
                status='draft',  # New workflow: start as draft
                created_by_id=current_user.id,
                created_at=str(date.today()),
                updated_at=datetime.now(),
                # Legacy field for backwards compatibility
                recorded_by=current_user.id,
            )
            db.session.add(col)
            db.session.flush()

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

            db.session.commit()
            flash(f"Collection saved as draft. Total amount: ₱{col.formatted_total_amount}", "success")
            return redirect(url_for(f"{app_name}.view_collection", collection_id=col.id))

    tender_id_pre = request.args.get("tender_id", type=int)
    lines = _outstanding_lines(tender_id_pre) if tender_id_pre else []
    outstanding_rows = []
    for tt in lines:
        collected = _collected(tt.id)
        outstanding = tt.amount - collected
        if outstanding > 0:
            outstanding_rows.append({"tt": tt, "outstanding": outstanding})

    context = {
        "app_label": app_label,
        "tenders": tenders,
        "bank_accounts": bank_accounts,
        "outstanding_rows": outstanding_rows,
        "selected_tender_id": tender_id_pre,
        "today": str(date.today()),
    }
    return render_template("collections/new_collection.html", **context)


# ---------------------------------------------------------------------------
# AJAX — load outstanding lines for a tender
# ---------------------------------------------------------------------------

@bp.route("/lines")
@login_required
def get_lines():
    from flask import jsonify
    tender_id = request.args.get("tender_id", type=int)
    if not tender_id:
        return jsonify([])
    lines = _outstanding_lines(tender_id)
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
    db.session.delete(col)
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
    """Submit a draft collection for approval (or auto-approve if admin)"""
    col = Collection.query.get_or_404(collection_id)

    if col.status != 'draft':
        flash('Only draft collections can be submitted.', 'danger')
        return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))

    # Check ownership
    if col.created_by_id != current_user.id and not current_user.is_admin:
        flash('You can only submit your own collections.', 'danger')
        return redirect(url_for(f'{app_name}.history'))

    # Admin auto-approve: If user is admin, automatically approve collection
    if current_user.is_admin:
        col.status = 'posted'
        col.submitted_by_id = current_user.id
        col.submitted_at = datetime.now()
        col.approved_by_id = current_user.id
        col.approved_at = datetime.now()
        col.updated_at = datetime.now()

        db.session.commit()

        flash(f'Collection auto-approved and posted! Total amount: ₱{col.formatted_total_amount}', 'success')
    else:
        # Regular user: submit for approval
        col.status = 'submitted'
        col.submitted_by_id = current_user.id
        col.submitted_at = datetime.now()
        col.updated_at = datetime.now()

        db.session.commit()

        flash(f'Collection submitted successfully! Waiting for admin approval. Total amount: ₱{col.formatted_total_amount}', 'success')

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

    db.session.commit()

    flash(f'Collection approved and posted! Total amount: ₱{col.formatted_total_amount}', 'success')
    return redirect(url_for(f'{app_name}.view_collection', collection_id=collection_id))


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

        col.status = 'cancelled'
        col.cancelled_by_id = current_user.id
        col.cancelled_at = datetime.now()
        col.cancellation_reason = reason
        col.updated_at = datetime.now()

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


