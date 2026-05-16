from dataclasses import dataclass, field
from sqlalchemy import func
from application.extensions import db
from .models import Transaction as Obj
from .models import TransactionDetail as ObjDetail
from .models import TransactionTender as ObjTender
from .admin_models import UserTransaction as Preparer
from datetime import datetime
from . import app_name

from ...register.customer import Customer
from ...register.product import Product
from ...register.tender import Tender


DETAIL_ROWS = 10
TENDER_ROWS = 5


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

    product_name: str = ""
    errors: dict = field(default_factory=dict)

    def _populate(self, row: ObjDetail):
        self.id = row.id
        self.product_id = row.product_id
        self.amount = float(row.amount)
        self.discount = float(row.discount)
        self.side_note = row.side_note or ""
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
        self.submitted = obj.submitted or ""
        self.cancelled = obj.cancelled or ""

        if obj.customer:
            self.customer_name = obj.customer.customer_name

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

        # Customer
        customer_name = request_form.get("customer_name", "")
        self.customer_name = customer_name
        customer = Customer.query.filter_by(customer_name=customer_name).first()
        self.customer_id = customer.id if customer else 0

        # Detail rows – HTML sends arrays: product_id[], amount[], etc.
        product_ids = request_form.getlist("product_id[]")
        amounts = request_form.getlist("amount[]")
        detail_discounts = request_form.getlist("detail_discount[]")
        side_notes = request_form.getlist("side_note[]")

        self.details = []
        for i in range(len(product_ids)):
            sub = DetailSubForm()
            sub.product_id = int(product_ids[i]) if product_ids[i] else 0
            sub.amount = _safe_float(amounts[i] if i < len(amounts) else 0)
            sub.discount = _safe_float(detail_discounts[i] if i < len(detail_discounts) else 0)
            sub.side_note = side_notes[i] if i < len(side_notes) else ""
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
            self.errors["customer_name"] = "Please enter a customer."
        else:
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

        # Tender total must equal (gross - discount)
        dirty_tenders = [sub for _, sub in self.tenders if sub._is_dirty()]
        if not dirty_tenders:
            self.errors["tenders"] = "At least one tender/payment is required."
        else:
            for _, sub in self.tenders:
                if sub._is_dirty() and not sub._validate():
                    tender_valid = False

        if not self.errors and detail_valid and tender_valid:
            gross = sum(sub.amount for _, sub in self.details if sub._is_dirty())
            detail_discount = sum(sub.discount for _, sub in self.details if sub._is_dirty())
            total_due = gross - detail_discount - self.discount
            total_tendered = sum(sub.amount for _, sub in self.tenders if sub._is_dirty())

            if round(total_due, 2) != round(total_tendered, 2):
                self.errors["totals"] = (
                    f"Total tendered ({total_tendered:,.2f}) must equal "
                    f"amount due ({total_due:,.2f})."
                )

        return not self.errors and detail_valid and tender_valid

    # ------------------------------------------------------------------ #
    # Save (create or update)                                              #
    # ------------------------------------------------------------------ #

    def _save(self):
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
            )
            db.session.add(record)
            db.session.flush()  # get record.id before committing
            self.id = record.id
        else:
            record = Obj.query.get(self.id)
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

    # ------------------------------------------------------------------ #
    # Submit / Cancel                                                      #
    # ------------------------------------------------------------------ #

    def _submit(self):
        record = Obj.query.get(self.id)
        record.submitted = str(datetime.today())[:10]
        self.submitted = record.submitted
        db.session.commit()

    def _cancel(self):
        record = Obj.query.get(self.id)
        record.cancelled = str(datetime.today())[:10]
        self.cancelled = record.cancelled
        db.session.commit()

    @property
    def _locked_(self):
        return bool(self.submitted or self.cancelled)