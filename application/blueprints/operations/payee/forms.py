from dataclasses import dataclass
from application.extensions import db
from application.blueprints.operations.daily_sales.models import Payee as Obj
from application.blueprints.audit.utils import log_create, log_update, model_to_dict


@dataclass
class Form:
    id: int = None
    name: str = ""
    description: str = ""
    active: bool = True

    errors: dict = None

    def __post_init__(self):
        self.errors = {}

    def _populate(self, row):
        self.id = row.id
        self.name = row.name or ""
        self.description = row.description or ""
        self.active = row.active

    def _post(self, f):
        record_id = f.get("record_id")
        self.id = int(record_id) if record_id else None
        self.name = (f.get("name") or "").strip()
        self.description = (f.get("description") or "").strip()
        self.active = "active" in f

    def _validate_on_submit(self):
        self.errors = {}
        if not self.name:
            self.errors["name"] = "Payee name is required."
        if not self.errors:
            return True
        return False

    def _save(self):
        is_new = self.id is None
        old_values = None

        if self.id is None:
            obj = Obj(
                name=self.name,
                description=self.description,
                active=self.active,
            )
            db.session.add(obj)
        else:
            obj = Obj.query.get(self.id)
            # Capture old values before updating
            old_values = model_to_dict(obj, ['name', 'description', 'active'])

            obj.name = self.name
            obj.description = self.description
            obj.active = self.active
        db.session.commit()

        # Audit logging
        try:
            if is_new:
                log_create(
                    module='payee',
                    record_id=obj.id,
                    record_identifier=f"{obj.name}",
                    new_values=model_to_dict(obj, ['name', 'description', 'active']),
                    notes='Payee created'
                )
            else:
                new_values = model_to_dict(obj, ['name', 'description', 'active'])
                log_update(
                    module='payee',
                    record_id=obj.id,
                    record_identifier=f"{obj.name}",
                    old_values=old_values,
                    new_values=new_values,
                    notes='Payee updated'
                )
            db.session.commit()
        except Exception as e:
            from flask import flash
            flash(f'Payee saved, but audit logging failed: {str(e)}', 'warning')
            print(f"Audit logging failed: {e}")

        return obj
