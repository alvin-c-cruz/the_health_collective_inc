from application.extensions import db
from .admin_models import AdminAccountType as ObjAdmin
from .admin_models import UserAccountType as ObjUser
from . import app_name

class AccountType(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    account_type_name = db.Column(db.String(255))

    account_class_id = db.Column(db.Integer, db.ForeignKey('account_class.id'), nullable=False)
    account_class = db.relationship('AccountClass', backref='account_class_details', lazy=True)

    priority = db.Column(db.String(255))

    def __str__(self):
        return getattr(self,f"{app_name}_name")
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
