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

    # Cancellation request fields
    cancellation_requested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cancellation_requested_by_user = db.relationship('User', foreign_keys=[cancellation_requested_by_id], backref='cancellation_requests_made')
    cancellation_requested_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.String(), nullable=True)
    cancellation_approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cancellation_approved_by_user = db.relationship('User', foreign_keys=[cancellation_approved_by_id], backref='cancellation_requests_approved')
    cancellation_approved_at = db.Column(db.DateTime, nullable=True)

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
    deductions = db.Column(db.Numeric(12, 2), default=0.00)  # Bank charges, fees, etc.
    deduction_details = db.Column(db.String())  # Description of what the deduction is for

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
    cancellation_reason = db.Column(db.String(), nullable=True)  # Why was this deposit cancelled

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
    def net_bank_credit(self):
        """Net amount credited to bank (total - deductions)"""
        return self.total_amount - float(self.deductions or 0)

    @property
    def formatted_net_bank_credit(self):
        return '{:,.2f}'.format(self.net_bank_credit)

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


class FundCategory(db.Model):
    """Categories of funds: Petty Cash, Change Fund, etc."""
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String())
    sort_order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<FundCategory {self.category_name}>'


class FundReceived(db.Model):
    """Funds received (incoming funds like replenishments)"""
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.String(), nullable=False)

    fund_category_id = db.Column(db.Integer, db.ForeignKey('fund_category.id'), nullable=False)
    fund_category = db.relationship('FundCategory', backref='funds_received', lazy=True)

    amount = db.Column(db.Float, default=0)
    reference_number = db.Column(db.String())
    description = db.Column(db.String())

    # Workflow fields
    status = db.Column(db.String(20), default='draft')  # draft | submitted | posted | cancelled
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by_user = db.relationship('User', foreign_keys=[created_by_id], backref='funds_received_created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    submitted_by_user = db.relationship('User', foreign_keys=[submitted_by_id], backref='funds_received_submitted')
    submitted_at = db.Column(db.DateTime, nullable=True)

    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by_user = db.relationship('User', foreign_keys=[approved_by_id], backref='funds_received_approved')
    approved_at = db.Column(db.DateTime, nullable=True)

    cancelled_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cancelled_by_user = db.relationship('User', foreign_keys=[cancelled_by_id], backref='funds_received_cancelled')
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.String(), nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def formatted_record_date(self):
        return short_date(self.record_date) if self.record_date else None

    @property
    def formatted_amount(self):
        return '{:,.2f}'.format(self.amount)

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


class FundDisbursed(db.Model):
    """Funds disbursed (outgoing funds like expenses)"""
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.String(), nullable=False)

    fund_category_id = db.Column(db.Integer, db.ForeignKey('fund_category.id'), nullable=False)
    fund_category = db.relationship('FundCategory', backref='funds_disbursed', lazy=True)

    amount = db.Column(db.Float, default=0)
    reference_number = db.Column(db.String())
    description = db.Column(db.String())

    # Workflow fields
    status = db.Column(db.String(20), default='draft')  # draft | submitted | posted | cancelled
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_by_user = db.relationship('User', foreign_keys=[created_by_id], backref='funds_disbursed_created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    submitted_by_user = db.relationship('User', foreign_keys=[submitted_by_id], backref='funds_disbursed_submitted')
    submitted_at = db.Column(db.DateTime, nullable=True)

    approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    approved_by_user = db.relationship('User', foreign_keys=[approved_by_id], backref='funds_disbursed_approved')
    approved_at = db.Column(db.DateTime, nullable=True)

    cancelled_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    cancelled_by_user = db.relationship('User', foreign_keys=[cancelled_by_id], backref='funds_disbursed_cancelled')
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.String(), nullable=True)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def formatted_record_date(self):
        return short_date(self.record_date) if self.record_date else None

    @property
    def formatted_amount(self):
        return '{:,.2f}'.format(self.amount)

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


# =============================================================================
# Petty Cash Management Models
# =============================================================================

class Payee(db.Model):
    """Payee for petty cash vouchers"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return self.name


class PettyCashVoucher(db.Model):
    """Petty Cash Voucher (PCV)"""
    __tablename__ = 'petty_cash_voucher'

    id = db.Column(db.Integer, primary_key=True)
    pcv_number = db.Column(db.String(50), unique=True, nullable=False)
    record_date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD format

    payee_id = db.Column(db.Integer, db.ForeignKey('payee.id'), nullable=False)
    payee = db.relationship('Payee', backref='vouchers')

    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)

    # Status workflow: draft -> submitted -> posted -> for_reimbursement -> reimbursed
    status = db.Column(db.String(20), default='draft')

    # Audit fields
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='pcvs_created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id], backref='pcvs_submitted')
    submitted_at = db.Column(db.DateTime)

    posted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    posted_by = db.relationship('User', foreign_keys=[posted_by_id], backref='pcvs_posted')
    posted_at = db.Column(db.DateTime)

    cancelled_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    cancelled_by = db.relationship('User', foreign_keys=[cancelled_by_id], backref='pcvs_cancelled')
    cancelled_at = db.Column(db.DateTime)
    cancelled_reason = db.Column(db.Text)

    # Link to reimbursement report when status becomes for_reimbursement
    reimbursement_report_id = db.Column(db.Integer, db.ForeignKey('reimbursement_report.id'))

    def __str__(self):
        return f"{self.pcv_number} - {self.payee.name if self.payee else 'N/A'}"

    @property
    def formatted_amount(self):
        return f"₱{self.amount:,.2f}"

    @property
    def formatted_date(self):
        return short_date(self.record_date)

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
    def is_for_reimbursement(self):
        return self.status == 'for_reimbursement'

    @property
    def is_reimbursed(self):
        return self.status == 'reimbursed'

    @property
    def is_cancelled(self):
        return self.status == 'cancelled'

    @property
    def can_edit(self):
        """Can only edit draft vouchers"""
        return self.status == 'draft'

    @property
    def can_submit(self):
        """Can submit draft vouchers"""
        return self.status == 'draft'

    @property
    def can_post(self):
        """Can post submitted vouchers"""
        return self.status == 'submitted'

    @property
    def can_cancel(self):
        """Can cancel before reimbursement"""
        return self.status in ['draft', 'submitted', 'posted']

    @property
    def can_add_to_reimbursement(self):
        """Can add to reimbursement report when posted"""
        return self.status == 'posted'


class ReimbursementReport(db.Model):
    """Reimbursement Report aggregating multiple PCVs"""
    __tablename__ = 'reimbursement_report'

    id = db.Column(db.Integer, primary_key=True)
    report_number = db.Column(db.String(50), unique=True, nullable=False)
    created_date = db.Column(db.String(10), nullable=False)

    period_start = db.Column(db.String(10))
    period_end = db.Column(db.String(10))

    total_amount = db.Column(db.Float, default=0)

    # Status: pending -> submitted -> reimbursed
    status = db.Column(db.String(20), default='pending')

    # Signatories
    prepared_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prepared_by = db.relationship('User', foreign_keys=[prepared_by_id], backref='reimbursement_reports_prepared')

    approved_by = db.Column(db.String(100), default='DGO')  # Default approver

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    submitted_at = db.Column(db.DateTime)

    # Relationships
    vouchers = db.relationship('PettyCashVoucher', backref='reimbursement_report', lazy=True)

    def __str__(self):
        return f"{self.report_number} - ₱{self.formatted_total_amount}"

    @property
    def formatted_total_amount(self):
        return f"{self.total_amount:,.2f}"

    @property
    def formatted_created_date(self):
        return short_date(self.created_date)

    @property
    def formatted_period(self):
        if self.period_start and self.period_end:
            return f"{short_date(self.period_start)} - {short_date(self.period_end)}"
        return "N/A"

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_submitted(self):
        return self.status == 'submitted'

    @property
    def is_reimbursed(self):
        return self.status == 'reimbursed'

    def calculate_total(self):
        """Calculate total from all linked vouchers"""
        self.total_amount = sum(v.amount for v in self.vouchers if v.amount)
        return self.total_amount


class ReimbursementReceived(db.Model):
    """Reimbursement received from bank/account"""
    __tablename__ = 'reimbursement_received'

    id = db.Column(db.Integer, primary_key=True)
    reference_number = db.Column(db.String(50), unique=True, nullable=False)
    record_date = db.Column(db.String(10), nullable=False)

    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=False)
    bank_account = db.relationship('BankAccount', backref='reimbursements')

    amount = db.Column(db.Float, nullable=False)
    notes = db.Column(db.Text)

    # Link to reimbursement report(s)
    reimbursement_report_id = db.Column(db.Integer, db.ForeignKey('reimbursement_report.id'))
    reimbursement_report = db.relationship('ReimbursementReport', backref='reimbursements_received')

    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='reimbursements_created')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __str__(self):
        return f"{self.reference_number} - ₱{self.formatted_amount}"

    @property
    def formatted_amount(self):
        return f"{self.amount:,.2f}"

    @property
    def formatted_date(self):
        return short_date(self.record_date)
