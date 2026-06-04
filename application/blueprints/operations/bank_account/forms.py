from dataclasses import dataclass
from application.extensions import db
from .models import BankAccount as Obj
from application.blueprints.audit.utils import log_create, log_update, model_to_dict


@dataclass
class Form:
    id:             int  = None
    bank_name:      str  = ""
    account_name:   str  = ""
    account_number: str  = ""
    display_name:   str  = ""
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
        self.display_name   = row.display_name or ""
        self.notes          = row.notes or ""
        self.active         = row.active

    def _post(self, f):
        record_id = f.get("record_id")
        self.id             = int(record_id) if record_id else None
        self.bank_name      = (f.get("bank_name") or "").strip()
        self.account_name   = (f.get("account_name") or "").strip()
        self.account_number = (f.get("account_number") or "").strip()
        self.display_name   = (f.get("display_name") or "").strip()
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
        is_new = self.id is None
        old_values = None

        if self.id is None:
            obj = Obj(
                bank_name=self.bank_name,
                account_name=self.account_name,
                account_number=self.account_number,
                display_name=self.display_name if self.display_name else f"{self.bank_name} — {self.account_number}",
                notes=self.notes,
                active=self.active,
            )
            db.session.add(obj)
        else:
            obj = Obj.query.get(self.id)
            # Capture old values before updating
            old_values = model_to_dict(obj, ['bank_name', 'account_name', 'account_number', 'display_name', 'notes', 'active'])

            obj.bank_name      = self.bank_name
            obj.account_name   = self.account_name
            obj.account_number = self.account_number
            obj.display_name   = self.display_name if self.display_name else f"{self.bank_name} — {self.account_number}"
            obj.notes          = self.notes
            obj.active         = self.active
        db.session.commit()

        # Audit logging
        try:
            if is_new:
                log_create(
                    module='bank_account',
                    record_id=obj.id,
                    record_identifier=f"{obj.bank_name} — {obj.account_number}",
                    new_values=model_to_dict(obj, ['bank_name', 'account_name', 'account_number', 'notes', 'active']),
                    notes='Bank account created'
                )
            else:
                new_values = model_to_dict(obj, ['bank_name', 'account_name', 'account_number', 'notes', 'active'])
                log_update(
                    module='bank_account',
                    record_id=obj.id,
                    record_identifier=f"{obj.bank_name} — {obj.account_number}",
                    old_values=old_values,
                    new_values=new_values,
                    notes='Bank account updated'
                )
            db.session.commit()
        except Exception as e:
            from flask import flash
            flash(f'Bank account saved, but audit logging failed: {str(e)}', 'warning')
            print(f"Audit logging failed: {e}")

        return obj
