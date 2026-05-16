from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from application.blueprints.user import login_required, roles_accepted
from application.extensions import db, ph_today

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

        collection_date = f.get("collection_date", str(ph_today()))
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
                recorded_by=current_user.id,
                created_at=str(ph_today()),
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
            flash("Collection recorded successfully.", "success")
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
        "today": str(ph_today()),
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

