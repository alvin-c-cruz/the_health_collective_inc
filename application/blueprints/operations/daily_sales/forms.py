from dataclasses import dataclass, field
from sqlalchemy import func
from application.extensions import db, ph_today
from .models import Transaction as Obj
from .models import TransactionDetail as ObjDetail
from .models import TransactionTender as ObjTender
from .admin_models import UserTransaction as Preparer
from datetime import datetime
from . import app_name
from .audit_logger import log_status_change, get_model_snapshot

# Centralized audit logging
from application.blueprints.audit.utils import (
    log_create as audit_log_create,
    log_update as audit_log_update,
    model_to_dict
)

from ...register.customer import Customer
from ...register.product import Product
from ...register.tender import Tender


DETAIL_ROWS = 100  # Support up to 100 line items per transaction
TENDER_ROWS = 20   # Support up to 20 payment methods per transaction


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# SubForm – one product line item
# ---------------------------------------------------------------------------

@dataclass
class DetailSubForm:
    id: int = 0
    product_id: int = 0
    amount: float = 0.0
    discount: float = 0.0
    side_note: str = ""
    billable: bool = True  # True = billable, False = inventory only

    product_name: str = ""
    errors: dict = field(default_factory=dict)

    def _populate(self, row: ObjDetail):
        self.id = row.id
        self.product_id = row.product_id
        self.amount = float(row.amount)
        self.discount = float(row.discount)
        self.side_note = row.side_note or ""
        self.billable = getattr(row, 'billable', True)  # Default to True for backward compatibility
        if row.product:
            self.product_name = row.product.product_name

    def _is_dirty(self):
        return bool(self.product_id or self.amount or self.side_note)

    def _validate(self):
        self.errors = {}
        if self._is_dirty():
            if not self.product_id:
                self.errors["product_id"] = "Please select a product."
            if self.amount < 0:
                self.errors["amount"] = "Amount cannot be negative."
            if self.discount < 0:
                self.errors["discount"] = "Discount cannot be negative."
            if self.discount > self.amount:
                self.errors["discount"] = "Discount cannot exceed amount."
        return not self.errors


# ---------------------------------------------------------------------------
# TenderSubForm – one payment line
# ---------------------------------------------------------------------------

@dataclass
class TenderSubForm:
    id: int = 0
    tender_id: int = 0
    amount: float = 0.0
    side_note: str = ""

    tender_name: str = ""
    errors: dict = field(default_factory=dict)

    def _populate(self, row: ObjTender):
        self.id = row.id
        self.tender_id = row.tender_id
        self.amount = float(row.amount)
        self.side_note = row.side_note or ""
        if row.tender:
            self.tender_name = row.tender.tender_name

    def _is_dirty(self):
        return bool(self.tender_id or self.amount)

    def _validate(self):
        self.errors = {}
        if self._is_dirty():
            if not self.tender_id:
                self.errors["tender_id"] = "Please select a tender type."
            if self.amount <= 0:
                self.errors["amount"] = "Tender amount must be greater than zero."
        return not self.errors


# ---------------------------------------------------------------------------
# Main Form
# ---------------------------------------------------------------------------

@dataclass
class Form:
    id: int = None
    record_date: str = ""
    record_number: str = ""
    dashlabs_number: str = ""
    pos_number: str = ""
    transaction_type_id: int = None
    ape_batch_id: int = None
    customer_id: int = 0
    prepared_by: str = ""
    checked_by: str = ""
    approved_by: str = ""
    description: str = ""
    discount: float = 0.0
    discount_description: str = ""

    submitted: str = ""
    cancelled: str = ""

    user_prepare_id: int = None
    customer_name: str = ""

    details: list = field(default_factory=list)
    tenders: list = field(default_factory=list)
    errors: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.details:
            self.details = [(i, DetailSubForm()) for i in range(DETAIL_ROWS)]
        if not self.tenders:
            self.tenders = [(i, TenderSubForm()) for i in range(TENDER_ROWS)]

    # ------------------------------------------------------------------ #
    # Populate from DB object                                              #
    # ------------------------------------------------------------------ #

    def _populate(self, obj: Obj):
        self.id = obj.id
        self.record_date = obj.record_date or ""
        self.record_number = obj.record_number or ""
        self.dashlabs_number = obj.dashlabs_number or ""
        self.pos_number = obj.pos_number or ""
        self.transaction_type_id = obj.transaction_type_id
        self.ape_batch_id = obj.ape_batch_id
        self.customer_id = obj.customer_id
        self.prepared_by = obj.prepared_by or ""
        self.checked_by = obj.checked_by or ""
        self.approved_by = obj.approved_by or ""
        self.description = obj.description or ""
        self.discount = float(obj.discount or 0)
        self.discount_description = obj.discount_description or ""
        self.submitted = obj.submitted or ""
        self.cancelled = obj.cancelled or ""

        if obj.customer:
            self.customer_name = str(obj.customer)  # Use formatted name: Last Name, First Name Middle Name

        self.details = [(i, DetailSubForm()) for i in range(DETAIL_ROWS)]
        for i, row in enumerate(obj.transaction_details):
            if i >= DETAIL_ROWS:
                break
            sub = DetailSubForm()
            sub._populate(row)
            self.details[i] = (i, sub)

        self.tenders = [(i, TenderSubForm()) for i in range(TENDER_ROWS)]
        for i, row in enumerate(obj.transaction_tenders):
            if i >= TENDER_ROWS:
                break
            sub = TenderSubForm()
            sub._populate(row)
            self.tenders[i] = (i, sub)

    # ------------------------------------------------------------------ #
    # Populate from request.form (POST)                                   #
    # ------------------------------------------------------------------ #

    def _post(self, request_form):
        record_id = request_form.get("record_id")
        self.id = int(record_id) if record_id else None

        self.record_date = request_form.get("record_date", "")
        self.record_number = request_form.get("record_number", "")
        self.dashlabs_number = request_form.get("dashlabs_number", "")
        self.pos_number = request_form.get("pos_number", "")
        raw_type_id = request_form.get("transaction_type_id")
        self.transaction_type_id = int(raw_type_id) if raw_type_id else None
        raw_batch_id = request_form.get("ape_batch_id")
        self.ape_batch_id = int(raw_batch_id) if raw_batch_id else None
        self.prepared_by = request_form.get("prepared_by", "")
        self.checked_by = request_form.get("checked_by", "")
        self.approved_by = request_form.get("approved_by", "")
        self.description = request_form.get("description", "")
        self.discount = _safe_float(request_form.get("discount"))
        self.discount_description = request_form.get("discount_description", "").strip()

        # Customer - find by formatted name or legacy customer_name
        customer_name = request_form.get("customer_name", "")
        self.customer_name = customer_name
        # First try to find by formatted name (all customers)
        customer = None
        for c in Customer.query.all():
            if str(c) == customer_name:
                customer = c
                break
        # Fallback to legacy customer_name field
        if not customer:
            customer = Customer.query.filter_by(customer_name=customer_name).first()
        self.customer_id = customer.id if customer else 0

        # Detail rows – HTML sends arrays: product_id[], amount[], etc.
        product_ids = request_form.getlist("product_id[]")
        amounts = request_form.getlist("amount[]")
        detail_discounts = request_form.getlist("detail_discount[]")
        side_notes = request_form.getlist("side_note[]")
        billable_values = request_form.getlist("billable[]")  # Hidden field updated by checkbox

        self.details = []
        for i in range(len(product_ids)):
            sub = DetailSubForm()
            sub.product_id = int(product_ids[i]) if product_ids[i] else 0
            sub.amount = _safe_float(amounts[i] if i < len(amounts) else 0)
            sub.discount = _safe_float(detail_discounts[i] if i < len(detail_discounts) else 0)
            sub.side_note = side_notes[i] if i < len(side_notes) else ""
            sub.billable = billable_values[i] == "1" if i < len(billable_values) else True
            self.details.append((i, sub))

        # Tender rows
        tender_ids = request_form.getlist("tender_id[]")
        tender_amounts = request_form.getlist("tender_amount[]")
        tender_notes = request_form.getlist("tender_note[]")

        self.tenders = []
        for i in range(len(tender_ids)):
            sub = TenderSubForm()
            sub.tender_id = int(tender_ids[i]) if tender_ids[i] else 0
            sub.amount = _safe_float(tender_amounts[i] if i < len(tender_amounts) else 0)
            sub.side_note = tender_notes[i] if i < len(tender_notes) else ""
            self.tenders.append((i, sub))

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #

    def _validate_on_submit(self):
        self.errors = {}
        detail_valid = True
        tender_valid = True

        if not self.record_date:
            self.errors["record_date"] = "Please enter a date."

        if not self.customer_name:
            self.errors["customer_name"] = "Please enter a patient."
        else:
            # Find by formatted name or legacy customer_name
            customer = None
            for c in Customer.query.all():
                if str(c) == self.customer_name:
                    customer = c
                    break
            if not customer:
                customer = Customer.query.filter_by(customer_name=self.customer_name).first()
            if not customer:
                self.errors["customer_name"] = f'"{self.customer_name}" not found.'

        # At least one dirty detail
        dirty_details = [sub for _, sub in self.details if sub._is_dirty()]
        if not dirty_details:
            self.errors["details"] = "At least one item is required."
        else:
            for _, sub in self.details:
                if sub._is_dirty() and not sub._validate():
                    detail_valid = False

        # Calculate total due first to determine if tenders are required
        # Only sum billable items (exclude inventory-only items)
        gross = sum(sub.amount for _, sub in self.details if sub._is_dirty() and getattr(sub, 'billable', True))
        detail_discount = sum(sub.discount for _, sub in self.details if sub._is_dirty() and getattr(sub, 'billable', True))
        total_due = gross - detail_discount - self.discount

        # Tender total must equal (gross - discount)
        # Tenders are optional when total_due is zero (all items non-billable)
        dirty_tenders = [sub for _, sub in self.tenders if sub._is_dirty()]
        if not dirty_tenders and total_due != 0:
            self.errors["tenders"] = "At least one tender/payment is required."
        else:
            for _, sub in self.tenders:
                if sub._is_dirty() and not sub._validate():
                    tender_valid = False

        if not self.errors and detail_valid and tender_valid:
            total_tendered = sum(sub.amount for _, sub in self.tenders if sub._is_dirty())

            # Only validate tender total match if there's an amount due
            if total_due != 0 and round(total_due, 2) != round(total_tendered, 2):
                self.errors["totals"] = (
                    f"Total tendered ({total_tendered:,.2f}) must equal "
                    f"amount due ({total_due:,.2f})."
                )

        return not self.errors and detail_valid and tender_valid

    # ------------------------------------------------------------------ #
    # Save (create or update)                                              #
    # ------------------------------------------------------------------ #

    def _save(self):
        is_new = self.id is None
        old_snapshot = None

        if self.id is None:
            record = Obj(
                record_date=self.record_date,
                record_number=self.record_number,
                dashlabs_number=self.dashlabs_number,
                pos_number=self.pos_number,
                transaction_type_id=self.transaction_type_id,
                ape_batch_id=self.ape_batch_id,
                customer_id=self.customer_id,
                prepared_by=self.prepared_by,
                checked_by=self.checked_by,
                approved_by=self.approved_by,
                description=self.description,
                discount=self.discount,
                discount_description=self.discount_description,
            )
            db.session.add(record)
            db.session.flush()  # get record.id before committing
            self.id = record.id
        else:
            record = Obj.query.get(self.id)
            # Capture old state before updating
            old_snapshot = get_model_snapshot(record)

            record.record_date = self.record_date
            record.record_number = self.record_number
            record.dashlabs_number = self.dashlabs_number
            record.pos_number = self.pos_number
            record.transaction_type_id = self.transaction_type_id
            record.ape_batch_id = self.ape_batch_id
            record.customer_id = self.customer_id
            record.prepared_by = self.prepared_by
            record.checked_by = self.checked_by
            record.approved_by = self.approved_by
            record.description = self.description
            record.discount = self.discount
            record.discount_description = self.discount_description

            # Delete existing details & tenders, then re-insert
            ObjDetail.query.filter_by(transaction_id=self.id).delete()
            ObjTender.query.filter_by(transaction_id=self.id).delete()

        # Insert details
        for _, sub in self.details:
            if sub._is_dirty():
                db.session.add(ObjDetail(
                    transaction_id=self.id,
                    product_id=sub.product_id,
                    amount=sub.amount,
                    discount=sub.discount,
                    side_note=sub.side_note,
                    billable=sub.billable,
                ))

        # Insert tenders
        for _, sub in self.tenders:
            if sub._is_dirty():
                db.session.add(ObjTender(
                    transaction_id=self.id,
                    tender_id=sub.tender_id,
                    amount=sub.amount,
                    side_note=sub.side_note,
                ))

        # Preparer (upsert)
        if self.user_prepare_id:
            preparer = Preparer.query.filter_by(transaction_id=self.id).first()
            if preparer:
                preparer.user_id = self.user_prepare_id
            else:
                db.session.add(Preparer(
                    transaction_id=self.id,
                    user_id=self.user_prepare_id,
                ))

        db.session.commit()

        # Audit logging
        try:
            from flask_login import current_user

            # Build transaction identifier
            customer_name = record.customer.customer_name if record.customer else 'No customer'
            txn_type = record.transaction_type.type_name if record.transaction_type else 'No type'

            # Calculate total amount
            total_amount = sum(t.amount for t in record.transaction_tenders)

            # Get tender names
            tender_names = ', '.join([t.tender.tender_name for t in record.transaction_tenders if t.tender])

            record_identifier = f"Transaction #{record.record_number} - {customer_name}"

            if is_new:
                # CREATE action
                notes = f"{txn_type} • Total: ₱{total_amount:,.2f} • {tender_names if tender_names else 'No tender'}"

                audit_log_create(
                    module='daily_sales',
                    record_id=record.id,
                    record_identifier=record_identifier,
                    new_values=model_to_dict(record, [
                        'record_date', 'record_number', 'dashlabs_number', 'pos_number',
                        'transaction_type_id', 'customer_id', 'discount', 'description', 'status'
                    ]),
                    notes=notes
                )
            elif old_snapshot:
                # UPDATE action
                new_snapshot = get_model_snapshot(record)
                notes = f"{txn_type} • Total: ₱{total_amount:,.2f} • {tender_names if tender_names else 'No tender'}"

                audit_log_update(
                    module='daily_sales',
                    record_id=record.id,
                    record_identifier=record_identifier,
                    old_values=old_snapshot,
                    new_values=new_snapshot,
                    notes=notes
                )

            db.session.commit()
        except Exception as e:
            # Don't fail the transaction save if audit logging fails, but warn user
            from flask import flash
            flash(f'Transaction saved, but audit logging failed: {str(e)}', 'warning')
            print(f"Audit logging failed: {e}")

    # ------------------------------------------------------------------ #
    # Submit / Cancel                                                      #
    # ------------------------------------------------------------------ #

    def _submit(self):
        record = Obj.query.get(self.id)
        record.submitted = str(ph_today())
        self.submitted = record.submitted
        db.session.commit()

        # Audit logging
        try:
            log_status_change('transaction', record, 'submitted', notes='Transaction submitted for approval')
            db.session.commit()
        except Exception as e:
            from flask import flash
            flash(f'Transaction submitted, but audit logging failed: {str(e)}', 'warning')
            print(f"Audit logging failed: {e}")

    def _cancel(self):
        record = Obj.query.get(self.id)
        record.cancelled = str(ph_today())
        self.cancelled = record.cancelled
        db.session.commit()

    def _uncancel(self):
        """Un-cancel a transaction - only allowed before submission"""
        record = Obj.query.get(self.id)
        if record.submitted:
            return False  # Cannot un-cancel submitted transactions
        record.cancelled = None
        self.cancelled = None
        db.session.commit()
        return True

    @property
    def _locked_(self):
        return bool(self.submitted or self.cancelled)
