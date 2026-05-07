from application.extensions import db
from .admin_models import AdminProductType as ObjAdmin
from .admin_models import UserProductType as ObjUser
from . import app_name

class ProductType(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    product_type_name = db.Column(db.String(255))

    def __str__(self):
        return self.product_type_name
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
