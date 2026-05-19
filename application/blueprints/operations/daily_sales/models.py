from datetime import datetime
from application.extensions import db, short_date, long_date
from .admin_models import AdminTransaction as ObjAdmin
from .admin_models import UserTransaction as ObjUser
from ..transaction_type.models import TransactionType


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.String())
    record_number = db.Column(db.String())
    dashlabs_number = db.Column(db.String())
    pos_number = db.Column(db.String())

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer', backref='transactions', lazy=True)

    # Legacy fields (keep for backward compatibility)
    prepared_by = db.Column(db.String())
    checked_by = db.Column(db.String())
    approved_by = db.Column(db.String())

    description = db.Column(db.String())

    transaction_type_id = db.Column(db.Integer, db.ForeignKey('transaction_type.id'), nullable=True)
    transaction_type = db.relationship('TransactionType', lazy=True)

    ape_batch_id = db.Column(db.Integer, db.ForeignKey('ape_batch.id'), nullable=True)
    ape_batch = db.relationship('ApeBatch', lazy=True, foreign_keys=[ape_batch_id])

    # Legacy submitted/cancelled fields
    submitted = db.Column(db.String())
    cancelled = db.Column(db.String())

    discount = db.Column(db.Float, default=0)

    # New workflow fields
    status = db.Column(db.String(20), default='draft')  # draft | submitted | posted
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by_user = db.relationship('User', foreign_keys=[created_by_id], backref='transactions_created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    submitted_by_user = db.relationship('User', foreign_keys=[submitted_by_id], backref='transactions_submitted')
    submitted_at = db.Column(db.DateTime, nullable=True)

    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by_user = db.relationship('User', foreign_keys=[approved_by_id], backref='transactions_approved')
    approved_at = db.Column(db.DateTime, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def preparer(self):
        return ObjUser.query.filter(ObjUser.transaction_id == self.id).first()

    @property
    def approved(self):
        return ObjAdmin.query.filter(ObjAdmin.transaction_id == self.id).first()

    @property
    def formatted_record_date(self):
        return short_date(self.record_date) if self.record_date else None

    @property
    def formatted_record_date_dr(self):
        return long_date(self.record_date) if self.record_date else None

    @property
    def formatted_submitted(self):
        return short_date(self.submitted) if self.submitted else None

    @property
    def formatted_cancelled(self):
        return short_date(self.cancelled) if self.cancelled else None

    @property
    def formatted_discount(self):
        return '{:,.2f}'.format(self.discount)

    def is_submitted(self):
        return True if self.submitted else False

    # New workflow status methods
    @property
    def is_draft(self):
        return self.status == 'draft'

    @property
    def is_status_submitted(self):
        return self.status == 'submitted'

    @property
    def is_posted(self):
        return self.status == 'posted'


class TransactionDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    transaction = db.relationship('Transaction', backref='transaction_details', lazy=True)

    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product = db.relationship('Product', backref='transaction_details', lazy=True)

    amount = db.Column(db.Float, default=0)
    discount = db.Column(db.Float, default=0)
    side_note = db.Column(db.String())

    @property
    def formatted_amount(self):
        return '{:,.2f}'.format(self.amount)

    @property
    def formatted_discount(self):
        return '{:,.2f}'.format(self.discount)


class TransactionTender(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    transaction = db.relationship('Transaction', backref='transaction_tenders', lazy=True)

    tender_id = db.Column(db.Integer, db.ForeignKey('tender.id'), nullable=False)
    tender = db.relationship('Tender', backref='transaction_tenders', lazy=True)

    amount = db.Column(db.Float, default=0)
    side_note = db.Column(db.String())

    @property
    def formatted_amount(self):
        return '{:,.2f}'.format(self.amount)


class Deposit(db.Model):
    """Bank deposit record linking cash sales to bank deposits"""
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.String())  # Deposit date
    reference_number = db.Column(db.String())  # Bank slip / ref no.
    bank_account = db.Column(db.String())  # Bank / Account name
    notes = db.Column(db.String())  # Optional notes

    # Workflow fields
    status = db.Column(db.String(20), default='draft')  # draft | submitted | posted | cancelled
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by_user = db.relationship('User', foreign_keys=[created_by_id], backref='deposits_created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    submitted_by_user = db.relationship('User', foreign_keys=[submitted_by_id], backref='deposits_submitted')
    submitted_at = db.Column(db.DateTime, nullable=True)

    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by_user = db.relationship('User', foreign_keys=[approved_by_id], backref='deposits_approved')
    approved_at = db.Column(db.DateTime, nullable=True)

    cancelled_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cancelled_by_user = db.relationship('User', foreign_keys=[cancelled_by_id], backref='deposits_cancelled')
    cancelled_at = db.Column(db.DateTime, nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def formatted_record_date(self):
        return short_date(self.record_date) if self.record_date else None

    @property
    def total_amount(self):
        """Total amount from all deposit items"""
        return sum(item.amount for item in self.deposit_items)

    @property
    def formatted_total_amount(self):
        return '{:,.2f}'.format(self.total_amount)

    @property
    def is_draft(self):
        return self.status == 'draft'

    @property
    def is_submitted(self):
        return self.status == 'submitted'

    @property
    def is_posted(self):
        return self.status == 'posted'

    @property
    def is_cancelled(self):
        return self.status == 'cancelled'


class DepositItem(db.Model):
    """Individual transactions included in a deposit"""
    id = db.Column(db.Integer, primary_key=True)

    deposit_id = db.Column(db.Integer, db.ForeignKey('deposit.id'), nullable=False)
    deposit = db.relationship('Deposit', backref='deposit_items', lazy=True)

    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=False)
    transaction = db.relationship('Transaction', backref='deposit_items', lazy=True)

    amount = db.Column(db.Float, default=0)  # Amount from this transaction included in deposit
    notes = db.Column(db.String())  # Optional notes per item

    @property
    def formatted_amount(self):
        return '{:,.2f}'.format(self.amount)
