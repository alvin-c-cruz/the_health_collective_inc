from dataclasses import dataclass
from application.extensions import db
from application.blueprints.operations.daily_sales.models import Payee as Obj


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
        if self.id is None:
            obj = Obj(
                name=self.name,
                description=self.description,
                active=self.active,
            )
            db.session.add(obj)
        else:
            obj = Obj.query.get(self.id)
            obj.name = self.name
            obj.description = self.description
            obj.active = self.active
        db.session.commit()
        return obj
