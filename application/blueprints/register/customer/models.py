from sqlalchemy.ext.hybrid import hybrid_property

from application.extensions import db

from . import app_name
from .admin_models import AdminCustomer as ObjAdmin
from .admin_models import UserCustomer as ObjUser


class Customer(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    _customer_name = db.Column(
        "customer_name", db.String(255)
    )  # Legacy field stored in DB
    last_name = db.Column(db.String(100))
    first_name = db.Column(db.String(100))
    middle_name = db.Column(db.String(100))
    tin = db.Column(db.String(255))
    address = db.Column(db.String(255))
    business_style = db.Column(db.String(), default="")
    birthday = db.Column(db.String())

    sex_id = db.Column(db.Integer, db.ForeignKey("sex.id"), nullable=False)
    sex = db.relationship("Sex", backref="customers", lazy=True)

    salesman = db.Column(db.String(), default="")

    @hybrid_property
    def customer_name(self):
        """Returns formatted name: Last Name, First Name Middle Name"""
        # Get actual string values, handling None
        last = getattr(self, "last_name", None) or ""
        first = getattr(self, "first_name", None) or ""
        middle = getattr(self, "middle_name", None) or ""

        # Ensure we have strings, not InstrumentedAttribute
        if not isinstance(last, str):
            last = ""
        if not isinstance(first, str):
            first = ""
        if not isinstance(middle, str):
            middle = ""

        if last or first:
            parts = []
            if last:
                parts.append(last)
            name_parts = []
            if first:
                name_parts.append(first)
            if middle:
                name_parts.append(middle)
            if name_parts:
                parts.append(" ".join(name_parts))
            return ", ".join(parts) if len(parts) > 1 else parts[0] if parts else ""

        # Fall back to legacy customer_name field
        legacy = getattr(self, "_customer_name", None)
        return legacy if isinstance(legacy, str) else ""

    @customer_name.expression
    def customer_name(cls):
        """SQL expression for ordering/filtering - uses last_name as primary sort"""
        from sqlalchemy import func

        # For SQL queries, order by last_name (most common sorting need)
        # If last_name is NULL/empty, fall back to legacy _customer_name field
        return func.coalesce(cls.last_name, cls._customer_name, "")

    @customer_name.setter
    def customer_name(self, value):
        """Setter for backwards compatibility"""
        self._customer_name = value

    def __str__(self):
        """Returns formatted name: Last Name, First Name Middle Name"""
        return self.customer_name

    @property
    def display_name(self):
        """Returns formatted name: Last Name, First Name Middle Name"""
        return self.customer_name

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
