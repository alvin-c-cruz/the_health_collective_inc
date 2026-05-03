from application.extensions import db
from .admin_models import AdminMeasure as ObjAdmin
from .admin_models import UserMeasure as ObjUser
from . import app_name

class Measure(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    measure_name = db.Column(db.String(255))

    def __str__(self):
        return self.measure_name
    
    @property
    def preparer(self):
        obj = ObjUser.query.filter(getattr(ObjUser,f"{app_name}_id")==self.id).first()
        return obj
    
    @property
    def approved(self):
        obj = ObjAdmin.query.filter(getattr(ObjAdmin,f"{app_name}_id")==self.id).first()
        return obj
