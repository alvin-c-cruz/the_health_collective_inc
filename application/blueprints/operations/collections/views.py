from datetime import date, datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
import openpyxl
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

    total_outstanding = sum(r["outstanding"] for r in rows if not r["is_settled"])

    context = {
        "app_label": app_label,
        "tenders": tenders,
        "selected_tender_id": tender_id,
        "rows": rows,
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
                recorded_by=current_user.id,
                created_at=str(date.today()),
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
# DSR Upload helpers
# ---------------------------------------------------------------------------

def _to_date_str(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.date().isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return str(val).strip() or None


def _norm(name):
    if not name:
        return ""
    return " ".join(str(name).upper().split())


# Collection section layout per sheet (all column indices are 1-based).
# amt_col is the Net Amount (after bank charges) for credit card sheets,
# or the full collection amount for HMO/APE sheets.
_DSR_SHEET_CFG = [
    dict(name="Walk-ins",     patient_col=4, date_col=11, ref_col=12, amt_col=16),
    dict(name="TELECONSULT",  patient_col=4, date_col=11, ref_col=12, amt_col=16),
    dict(name="HOME SERVICE", patient_col=4, date_col=10, ref_col=11, amt_col=15),
    dict(name="HMO-PHIC",     patient_col=3, date_col=15, ref_col=16, amt_col=17,
         hmo_cols={8: "Philhealth", 9: "Hive Health", 10: "Dynamic Care",
                   11: "Forticare", 12: "Asian Care"}),
    dict(name="MEDIPAD",      patient_col=4, date_col=20, ref_col=21, amt_col=22,
         hmo_cols={13: "Philhealth", 14: "Hive Health", 15: "Dynamic Care",
                   16: "Forticare", 17: "Asian Care"}),
    dict(name="APE",          patient_col=3, date_col=9,  ref_col=10, amt_col=12),
]


def _parse_dsr_excel(wb):
    """Return a flat list of collection rows found across all known DSR sheets."""
    rows = []
    for cfg in _DSR_SHEET_CFG:
        if cfg["name"] not in wb.sheetnames:
            continue
        ws = wb[cfg["name"]]
        hmo_cols = cfg.get("hmo_cols", {})

        for row_num in range(4, ws.max_row + 1):
            col_date = _to_date_str(ws.cell(row=row_num, column=cfg["date_col"]).value)
            if not col_date:
                continue
            try:
                amt = float(ws.cell(row=row_num, column=cfg["amt_col"]).value or 0)
            except (TypeError, ValueError):
                continue
            if amt <= 0:
                continue

            tx_date = _to_date_str(ws.cell(row=row_num, column=1).value)
            if not tx_date:
                continue

            patient_raw = str(ws.cell(row=row_num, column=cfg["patient_col"]).value or "").strip()
            ref_raw = ws.cell(row=row_num, column=cfg["ref_col"]).value
            reference = str(ref_raw).strip() if ref_raw else ""

            # For HMO sheets, detect which HMO column has a value → tender hint
            tender_hint = None
            for col_idx, tender_name in hmo_cols.items():
                try:
                    if float(ws.cell(row=row_num, column=col_idx).value or 0) > 0:
                        tender_hint = tender_name
                        break
                except (TypeError, ValueError):
                    pass

            rows.append(dict(
                sheet=cfg["name"],
                row_num=row_num,
                tx_date=tx_date,
                patient_raw=patient_raw,
                patient=_norm(patient_raw),
                col_date=col_date,
                reference=reference,
                amount=amt,
                tender_hint=tender_hint,
            ))
    return rows


def _match_row(row):
    """
    Match a parsed DSR row to a TransactionTender.
    Returns (tt, reason_or_'ok').
    """
    from ..daily_sales.models import Transaction

    txns = Transaction.query.filter(
        Transaction.record_date == row["tx_date"],
        Transaction.submitted.isnot(None),
        Transaction.cancelled.is_(None),
    ).all()

    matched_txn = next(
        (t for t in txns if t.customer and _norm(t.customer.customer_name) == row["patient"]),
        None,
    )
    if not matched_txn:
        return None, f"No submitted transaction on {row['tx_date']} for \"{row['patient_raw']}\""

    receivable_tts = [tt for tt in matched_txn.transaction_tenders
                      if tt.tender and tt.tender.is_receivable]
    if not receivable_tts:
        return None, "Transaction has no receivable tender"

    if row["tender_hint"]:
        hint = row["tender_hint"].lower()
        for tt in receivable_tts:
            if tt.tender.tender_name.lower() == hint:
                return tt, "ok"

    if len(receivable_tts) == 1:
        return receivable_tts[0], "ok"

    names = ", ".join(tt.tender.tender_name for tt in receivable_tts)
    return None, f"Multiple receivable tenders ({names}) — cannot auto-select"


# ---------------------------------------------------------------------------
# DSR Upload routes
# ---------------------------------------------------------------------------

@bp.route("/upload-dsr", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def upload_dsr():
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()

    if request.method == "GET":
        return render_template("collections/upload_dsr.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    uploaded = request.files.get("xlsx_file")
    if not uploaded or not uploaded.filename.endswith(".xlsx"):
        flash("Please upload a valid .xlsx file.", "danger")
        return render_template("collections/upload_dsr.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    bank_account_id = request.form.get("bank_account_id", type=int) or None

    try:
        wb = openpyxl.load_workbook(uploaded, data_only=True)
    except Exception as e:
        flash(f"Could not read file: {e}", "danger")
        return render_template("collections/upload_dsr.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    parsed = _parse_dsr_excel(wb)
    if not parsed:
        flash("No collection entries found. Fill in Collection Date and Amount in the DSR file.", "warning")
        return render_template("collections/upload_dsr.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    matched, unmatched = [], []
    for row in parsed:
        tt, reason = _match_row(row)
        if tt:
            already = _collected(tt.id)
            matched.append({**row, "tt": tt, "already_collected": already,
                            "outstanding": round(tt.amount - already, 2)})
        else:
            unmatched.append({**row, "reason": reason})

    return render_template("collections/upload_dsr_preview.html",
                           app_label=app_label,
                           matched=matched,
                           unmatched=unmatched,
                           bank_account_id=bank_account_id,
                           bank_accounts=bank_accounts)


@bp.route("/upload-dsr/confirm", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def confirm_dsr_upload():
    from collections import OrderedDict

    bank_account_id = request.form.get("bank_account_id", type=int) or None
    col_dates  = request.form.getlist("col_date")
    references = request.form.getlist("reference")
    tt_ids     = request.form.getlist("tt_id")
    amounts    = request.form.getlist("amount")

    if not tt_ids:
        flash("No data to save.", "warning")
        return redirect(url_for(f"{app_name}.upload_dsr"))

    tt_id_ints = [int(x) for x in tt_ids]
    tt_map = {tt.id: tt for tt in
              TransactionTender.query.filter(TransactionTender.id.in_(tt_id_ints)).all()}

    batches = OrderedDict()
    for col_date, ref, tt_id, amt in zip(col_dates, references, tt_id_ints, amounts):
        try:
            amt = float(amt)
        except (ValueError, TypeError):
            continue
        batches.setdefault((col_date, ref), []).append({"tt_id": tt_id, "amount": amt})

    created = 0
    for (col_date, reference), lines in batches.items():
        first_tt = tt_map.get(lines[0]["tt_id"])
        if not first_tt:
            continue
        col = Collection(
            collection_date=col_date,
            tender_id=first_tt.tender_id,
            bank_account_id=bank_account_id,
            reference=reference,
            recorded_by=current_user.id,
            created_at=str(date.today()),
        )
        db.session.add(col)
        db.session.flush()
        for r in lines:
            db.session.add(CollectionDetail(
                collection_id=col.id,
                transaction_tender_id=r["tt_id"],
                amount_applied=r["amount"],
            ))
        created += 1

    db.session.commit()
    flash(f"{created} collection batch(es) recorded from DSR.", "success")
    return redirect(url_for(f"{app_name}.history"))
