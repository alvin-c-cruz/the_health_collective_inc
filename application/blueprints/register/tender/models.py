from application.extensions import db

from . import app_name
from .admin_models import AdminTender as ObjAdmin
from .admin_models import UserTender as ObjUser


class Tender(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    tender_name = db.Column(db.String(255))
    symbol = db.Column(db.String(50))
    transaction_types = db.Column(
        db.String(255)
    )  # comma-separated type codes e.g. walk_in,ape,dialysis
    sort_order = db.Column(db.Integer, default=0)
    report_static = db.Column(db.Boolean, default=False)
    is_receivable = db.Column(db.Boolean, default=False)

    def has_transaction_type(self, txn_type):
        if not self.transaction_types:
            return False
        return txn_type in self.transaction_types.split(",")

    def __str__(self):
        return self.tender_name

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
