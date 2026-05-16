from application.extensions import db, short_date, long_date
from .admin_models import AdminTransaction as ObjAdmin
from .admin_models import UserTransaction as ObjUser


class TransactionType(db.Model):
    __tablename__ = 'transaction_type'
    id = db.Column(db.Integer, primary_key=True)
    type_code = db.Column(db.String(), unique=True, nullable=False)
    type_name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), default='')
    icon = db.Column(db.String(), default='bi-tag')
    icon_color = db.Column(db.String(), default='ic-blue')
    badge_color = db.Column(db.String(), default='thc-badge-blue')
    report_category = db.Column(db.String(), default='walk_in')
    active = db.Column(db.Boolean(), default=True)
    sort_order = db.Column(db.Integer(), default=99)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.String())
    record_number = db.Column(db.String())
    dashlabs_number = db.Column(db.String())
    pos_number = db.Column(db.String())

    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    customer = db.relationship('Customer', backref='transactions', lazy=True)

    prepared_by = db.Column(db.String())
    checked_by = db.Column(db.String())
    approved_by = db.Column(db.String())

    description = db.Column(db.String())

    transaction_type = db.Column(db.String(), default='walk_in')

    submitted = db.Column(db.String())
    cancelled = db.Column(db.String())

    discount = db.Column(db.Float, default=0)

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