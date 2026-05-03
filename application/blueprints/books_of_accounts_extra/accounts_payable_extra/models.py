from application.extensions import db, short_date, long_date
from .admin_models import AdminAccountsPayableExtra as ObjAdmin
from .admin_models import UserAccountsPayableExtra as ObjUser
from . import app_name

class AccountsPayableExtra(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    record_date = db.Column(db.String())
    record_number = db.Column(db.String())
    invoice_number = db.Column(db.String())
    rr_number = db.Column(db.String())
    po_number = db.Column(db.String())

    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    vendor = db.relationship('Vendor', backref='accounts_payable_extras', lazy=True)


    prepared_by = db.Column(db.String())
    checked_by = db.Column(db.String())
    approved_by = db.Column(db.String())

    description = db.Column(db.String())

    submitted = db.Column(db.String())
    cancelled = db.Column(db.String())

    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj

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
    
    def is_submitted(self):
        return True if self.submitted else False


class AccountsPayableExtraDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    accounts_payable_extra_id = db.Column(db.Integer, db.ForeignKey('accounts_payable_extra.id'), nullable=False)
    accounts_payable_extra = db.relationship('AccountsPayableExtra', backref='accounts_payable_extra_details', lazy=True)

    account_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    account = db.relationship('Account', backref='accounts_payable_extra_details', lazy=True)

    debit = db.Column(db.Float, default=0)
    credit = db.Column(db.Float, default=0)

    side_note = db.Column(db.String())

    @property
    def formatted_debit(self):
        return '{:,.2f}'.format(self.debit)

    @property
    def formatted_credit(self):
        return '{:,.2f}'.format(self.credit)
