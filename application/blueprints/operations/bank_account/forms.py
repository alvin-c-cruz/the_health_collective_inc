from dataclasses import dataclass
from application.extensions import db
from .models import BankAccount as Obj


@dataclass
class Form:
    id:             int  = None
    bank_name:      str  = ""
    account_name:   str  = ""
    account_number: str  = ""
    notes:          str  = ""
    active:         bool = True

    errors: dict = None

    def __post_init__(self):
        self.errors = {}

    def _populate(self, row):
        self.id             = row.id
        self.bank_name      = row.bank_name or ""
        self.account_name   = row.account_name or ""
        self.account_number = row.account_number or ""
        self.notes          = row.notes or ""
        self.active         = row.active

    def _post(self, f):
        record_id = f.get("record_id")
        self.id             = int(record_id) if record_id else None
        self.bank_name      = (f.get("bank_name") or "").strip()
        self.account_name   = (f.get("account_name") or "").strip()
        self.account_number = (f.get("account_number") or "").strip()
        self.notes          = (f.get("notes") or "").strip()
        self.active         = "active" in f

    def _validate_on_submit(self):
        self.errors = {}
        if not self.bank_name:
            self.errors["bank_name"] = "Bank name is required."
        if not self.errors:
            return True
        return False

    def _save(self):
        if self.id is None:
            obj = Obj(
                bank_name=self.bank_name,
                account_name=self.account_name,
                account_number=self.account_number,
                notes=self.notes,
                active=self.active,
            )
            db.session.add(obj)
        else:
            obj = Obj.query.get(self.id)
            obj.bank_name      = self.bank_name
            obj.account_name   = self.account_name
            obj.account_number = self.account_number
            obj.notes          = self.notes
            obj.active         = self.active
        db.session.commit()
        return obj
