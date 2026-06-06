from application.extensions import db

from .admin_models import AdminCompany as ObjAdmin
from .admin_models import UserCompany as ObjUser


class Company(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    company_name = db.Column(db.String(255))
    contact_person = db.Column(db.String(255))
    contact_number = db.Column(db.String(100))
    address = db.Column(db.String(500))
    tin = db.Column(db.String(50))
    active = db.Column(db.Boolean(), default=True)

    def __str__(self):
        return self.company_name

    @property
    def preparer(self):
        return ObjUser.query.filter(ObjUser.company_id == self.id).first()

    @property
    def approved(self):
        return ObjAdmin.query.filter(ObjAdmin.company_id == self.id).first()
