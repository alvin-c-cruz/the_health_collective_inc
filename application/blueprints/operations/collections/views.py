from datetime import date, datetime
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, send_file
from flask_login import current_user
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment

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
# Download Excel template
# ---------------------------------------------------------------------------

@bp.route("/template/download")
@login_required
@roles_accepted([ROLES_ACCEPTED])
def download_template():
    tender_id = request.args.get("tender_id", type=int)

    lines = _outstanding_lines(tender_id)
    rows = []
    for tt in lines:
        collected = _collected(tt.id)
        outstanding = round(tt.amount - collected, 2)
        if outstanding > 0:
            rows.append((tt, outstanding))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Collections"

    # --- styles ---
    header_font  = Font(bold=True, color="FFFFFF")
    header_fill  = PatternFill("solid", fgColor="1a4a6b")
    locked_fill  = PatternFill("solid", fgColor="F2F2F2")
    input_fill   = PatternFill("solid", fgColor="FFFDE7")
    center       = Alignment(horizontal="center", vertical="center")
    right        = Alignment(horizontal="right")

    # --- instruction row ---
    ws.merge_cells("A1:J1")
    ws["A1"] = (
        "INSTRUCTIONS: Fill in Collection Date, Reference, and Amount Applied "
        "for each line you are settling. Leave blank to skip. Do not edit columns A–G."
    )
    ws["A1"].font = Font(italic=True, color="555555")

    # --- column headers (row 2) ---
    headers = [
        ("TT_ID",           7),
        ("Date",           12),
        ("OR #",           10),
        ("Patient",        28),
        ("Tender",         18),
        ("Amount",         12),
        ("Outstanding",    13),
        ("Collection Date",14),
        ("Reference",      18),
        ("Amount Applied", 14),
    ]
    for col_idx, (label, width) in enumerate(headers, start=1):
        cell = ws.cell(row=2, column=col_idx, value=label)
        cell.font     = header_font
        cell.fill     = header_fill
        cell.alignment = center
        ws.column_dimensions[cell.column_letter].width = width

    # --- data rows ---
    for row_idx, (tt, outstanding) in enumerate(rows, start=3):
        t = tt.transaction
        record_date = t.record_date or ""
        record_number = t.record_number or ""
        patient = t.customer.customer_name if t.customer else ""
        tender_name = tt.tender.tender_name if tt.tender else ""

        values = [tt.id, record_date, record_number, patient, tender_name,
                  tt.amount, outstanding, None, None, outstanding]

        for col_idx, val in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            if col_idx <= 7:
                cell.fill      = locked_fill
                cell.alignment = right if col_idx in (6, 7) else cell.alignment
            else:
                cell.fill = input_fill
            if col_idx in (6, 7, 10):
                cell.number_format = "#,##0.00"

    # Freeze header rows
    ws.freeze_panes = "A3"

    # Lock hint: grey out ID column
    ws.column_dimensions["A"].hidden = False

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)

    filename = f"collections_template_{date.today().isoformat()}.xlsx"
    return send_file(stream, as_attachment=True, download_name=filename,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ---------------------------------------------------------------------------
# Upload Excel template
# ---------------------------------------------------------------------------

@bp.route("/upload", methods=["GET", "POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def upload_collections():
    bank_accounts = BankAccount.query.filter_by(active=True).order_by(BankAccount.bank_name).all()

    if request.method == "GET":
        return render_template("collections/upload.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    # ---- POST: parse file ----
    uploaded = request.files.get("xlsx_file")
    if not uploaded or not uploaded.filename.endswith(".xlsx"):
        flash("Please upload a valid .xlsx file.", "danger")
        return render_template("collections/upload.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    bank_account_id = request.form.get("bank_account_id", type=int) or None
    action          = request.form.get("action", "preview")

    try:
        wb = openpyxl.load_workbook(uploaded, data_only=True)
        ws = wb.active
    except Exception as e:
        flash(f"Could not read file: {e}", "danger")
        return render_template("collections/upload.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    # Read data rows (skip rows 1 and 2 which are instruction + header)
    parsed = []
    errors = []
    for row in ws.iter_rows(min_row=3, values_only=True):
        tt_id, rec_date, rec_num, patient, tender_name, amount, outstanding, \
            col_date, reference, amt_applied = (list(row) + [None]*10)[:10]

        if tt_id is None:
            continue
        if col_date is None or amt_applied is None:
            continue  # not filled in — skip

        # Normalise collection date
        if isinstance(col_date, datetime):
            col_date = col_date.date().isoformat()
        elif isinstance(col_date, date):
            col_date = col_date.isoformat()
        else:
            col_date = str(col_date).strip()

        try:
            amt_applied = float(amt_applied)
        except (ValueError, TypeError):
            errors.append(f"Row with TT_ID={tt_id}: invalid Amount Applied '{amt_applied}'.")
            continue

        if amt_applied <= 0:
            continue

        reference = str(reference).strip() if reference else ""

        parsed.append({
            "tt_id":      int(tt_id),
            "col_date":   col_date,
            "reference":  reference,
            "amt_applied": amt_applied,
            "patient":    patient or "",
            "rec_num":    rec_num or "",
        })

    if not parsed:
        flash("No collection rows found in the file. Make sure Collection Date and Amount Applied are filled in.", "warning")
        return render_template("collections/upload.html",
                               app_label=app_label, bank_accounts=bank_accounts)

    # Validate TransactionTender IDs
    tt_ids = [r["tt_id"] for r in parsed]
    tt_map = {tt.id: tt for tt in TransactionTender.query.filter(TransactionTender.id.in_(tt_ids)).all()}
    valid_rows = []
    for r in parsed:
        if r["tt_id"] not in tt_map:
            errors.append(f"TT_ID {r['tt_id']} not found — row skipped.")
        else:
            valid_rows.append(r)

    # Group by (col_date, reference) → collection batches
    from collections import OrderedDict
    batches = OrderedDict()
    for r in valid_rows:
        key = (r["col_date"], r["reference"])
        batches.setdefault(key, []).append(r)

    # Build preview structure
    preview = []
    for (col_date, reference), lines in batches.items():
        tender_ids = {tt_map[r["tt_id"]].tender_id for r in lines}
        tender_names = list({tt_map[r["tt_id"]].tender.tender_name for r in lines
                             if tt_map[r["tt_id"]].tender})
        preview.append({
            "col_date":    col_date,
            "reference":   reference,
            "tender_names": tender_names,
            "lines":       lines,
            "total":       sum(r["amt_applied"] for r in lines),
        })

    return render_template("collections/upload_preview.html",
                           app_label=app_label,
                           preview=preview,
                           errors=errors,
                           bank_accounts=bank_accounts,
                           bank_account_id=bank_account_id,
                           tt_map=tt_map)



@bp.route("/upload/confirm", methods=["POST"])
@login_required
@roles_accepted([ROLES_ACCEPTED])
def confirm_upload():
    """Save collection batches submitted from the preview page hidden fields."""
    bank_account_id = request.form.get("bank_account_id", type=int) or None

    col_dates    = request.form.getlist("col_date")
    references   = request.form.getlist("reference")
    tt_ids       = request.form.getlist("tt_id")
    amts_applied = request.form.getlist("amt_applied")

    if not tt_ids:
        flash("No data to save.", "warning")
        return redirect(url_for(f"{app_name}.upload_collections"))

    # Re-fetch TransactionTender records
    tt_id_ints = [int(x) for x in tt_ids]
    tt_map = {tt.id: tt for tt in TransactionTender.query.filter(TransactionTender.id.in_(tt_id_ints)).all()}

    # Rebuild batches from parallel lists
    from collections import OrderedDict
    batches = OrderedDict()
    for col_date, reference, tt_id, amt in zip(col_dates, references, tt_id_ints, amts_applied):
        key = (col_date, reference)
        try:
            amt = float(amt)
        except (ValueError, TypeError):
            continue
        batches.setdefault(key, []).append({"tt_id": tt_id, "amt_applied": amt})

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
                amount_applied=r["amt_applied"],
            ))
        created += 1

    db.session.commit()
    flash(f"{created} collection batch(es) recorded successfully.", "success")
    return redirect(url_for(f"{app_name}.history"))
