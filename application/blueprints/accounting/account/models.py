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
    
    def balance(self):
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
            _balance += sum(d.debit - d.credit for d in getattr(self,f"{book}_details" ))
            
        return _balance
    
    def formatted_balance(self):
        return '{:,.2f}'.format(self.balance())
    
    def debit_balance(self):
        if self.balance() > 0:
            return self.balance()
        else:
            return 0
        
    def credit_balance(self):
        if self.balance() < 0:
            return -self.balance()
        else:
            return 0

    def formatted_debit_balance(self):
        return '{:,.2f}'.format(self.debit_balance())
    
    def formatted_credit_balance(self):
        return '{:,.2f}'.format(self.credit_balance())
        

