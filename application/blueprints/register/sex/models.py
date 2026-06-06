from application.extensions import db

from . import app_name
from .admin_models import AdminSex as ObjAdmin
from .admin_models import UserSex as ObjUser


class Sex(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    sex_name = db.Column(db.String(255))

    def __str__(self):
        return self.sex_name

    @property
    def preparer(self):
        obj = ObjUser.query.filter(
            getattr(ObjUser, f"{app_name}_id") == self.id
        ).first()
        return obj

    @property
    def approved(self):
        obj = ObjAdmin.query.filter(
            getattr(ObjAdmin, f"{app_name}_id") == self.id
        ).first()
        return obj
