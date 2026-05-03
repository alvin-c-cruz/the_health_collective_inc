from application.extensions import db
from .admin_models import AdminCustomer as ObjAdmin
from .admin_models import UserCustomer as ObjUser
from . import app_name

class Customer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    customer_name = db.Column(db.String(255))
    tin = db.Column(db.String(255))
    address = db.Column(db.String(255))
    business_style = db.Column(db.String(), default="")
    salesman = db.Column(db.String(), default="")

    def __str__(self):
        return self.customer_name
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
