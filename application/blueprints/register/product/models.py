from application.extensions import db
from .admin_models import AdminProduct as ObjAdmin
from .admin_models import UserProduct as ObjUser
from . import app_name

class Product(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    product_name = db.Column(db.String(255))

    def __str__(self):
        return self.product_name
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
