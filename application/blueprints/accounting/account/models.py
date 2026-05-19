from application.extensions import db
from .admin_models import AdminAccount as ObjAdmin
from .admin_models import UserAccount as ObjUser
from . import app_name

class Account(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    account_number = db.Column(db.String(255))
    account_title = db.Column(db.String(255))
    account_description = db.Column(db.String(255))
    
    account_type_id = db.Column(db.Integer, db.ForeignKey('account_type.id'), nullable=True)
    account_type = db.relationship('AccountType', backref='account_type_details', lazy=True)

    def __str__(self):
        return f"{self.account_number}: {self.account_title}"
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def account_name(self):
        return f"{self.account_number}: {self.account_title}"
    
    def balance(self, as_of_date=None):
        """
        Calculate balance up to and including the specified date.
        If as_of_date is None, calculate all-time balance.
        """
        books = [
            "sales",
            "receipt",
            "accounts_payable",
            "disbursement",
            "general",
            "sales_extra",
            "receipt_extra",
            "accounts_payable_extra",
            "disbursement_extra",
            "general_extra",
            ]

        _balance = 0
        for book in books:
            details = getattr(self, f"{book}_details")
            for d in details:
                # Get the parent record (sales, receipt, etc.)
                parent = getattr(d, book)
                if parent and hasattr(parent, 'record_date'):
                    # Filter by date if as_of_date is provided
                    if as_of_date is None or (parent.record_date and parent.record_date <= as_of_date):
                        _balance += (d.debit - d.credit)
                else:
                    # If no date field, include all records
                    _balance += (d.debit - d.credit)

        return _balance

    def formatted_balance(self, as_of_date=None):
        return '{:,.2f}'.format(self.balance(as_of_date))

    def debit_balance(self, as_of_date=None):
        bal = self.balance(as_of_date)
        if bal > 0:
            return bal
        else:
            return 0

    def credit_balance(self, as_of_date=None):
        bal = self.balance(as_of_date)
        if bal < 0:
            return -bal
        else:
            return 0

    def formatted_debit_balance(self, as_of_date=None):
        return '{:,.2f}'.format(self.debit_balance(as_of_date))

    def formatted_credit_balance(self, as_of_date=None):
        return '{:,.2f}'.format(self.credit_balance(as_of_date))
        

