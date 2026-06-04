from dataclasses import dataclass
from sqlalchemy import func
from application.extensions import db
from .models import Company as Obj
from .admin_models import UserCompany as Preparer
from . import app_name
from application.blueprints.audit.utils import (
    log_create, log_update, log_delete,
    model_to_dict, get_record_identifier
)


@dataclass
class Form:
    id: int = None
    company_name: str = ""
    contact_person: str = ""
    contact_number: str = ""
    address: str = ""
    active: bool = True

    user_prepare_id: int = None
    errors = {}

    def _populate(self, row):
        self.id = row.id
        self.company_name = row.company_name or ""
        self.contact_person = row.contact_person or ""
        self.contact_number = row.contact_number or ""
        self.address = row.address or ""
        self.active = row.active

    def _post(self, request_form, current_user_id):
        record_id = request_form.get("record_id")
        self.id = int(record_id) if record_id else None
        self.company_name = (request_form.get("company_name") or "").upper().strip()
        self.contact_person = (request_form.get("contact_person") or "").strip()
        self.contact_number = (request_form.get("contact_number") or "").strip()
        self.address = (request_form.get("address") or "").strip()
        self.active = request_form.get("active") == "1"
        self.user_prepare_id = current_user_id

    def _save(self):
        if self.id is None:
            obj = Obj(
                company_name=self.company_name,
                contact_person=self.contact_person,
                contact_number=self.contact_number,
                address=self.address,
                active=self.active,
            )
            db.session.add(obj)
            db.session.flush()

            # Log creation after flush to get ID
            log_create(
                module='company',
                record_id=obj.id,
                record_identifier=str(obj),
                new_values=model_to_dict(obj, [
                    'company_name', 'contact_person', 'contact_number', 'address', 'tin', 'active'
                ]),
                notes='Company created'
            )

            db.session.commit()
            db.session.add(Preparer(company_id=obj.id, user_id=self.user_prepare_id))
            db.session.commit()
        else:
            obj = Obj.query.get(self.id)

            # Capture old values before update
            old_values = model_to_dict(obj, [
                'company_name', 'contact_person', 'contact_number', 'address', 'tin', 'active'
            ])

            obj.company_name = self.company_name
            obj.contact_person = self.contact_person
            obj.contact_number = self.contact_number
            obj.address = self.address
            obj.active = self.active

            # Capture new values after update
            new_values = model_to_dict(obj, [
                'company_name', 'contact_person', 'contact_number', 'address', 'tin', 'active'
            ])

            # Log update before commit
            log_update(
                module='company',
                record_id=obj.id,
                record_identifier=str(obj),
                old_values=old_values,
                new_values=new_values
            )

            preparer = Preparer.query.filter_by(company_id=self.id).first()
            if preparer:
                preparer.user_id = self.user_prepare_id
            else:
                db.session.add(Preparer(company_id=self.id, user_id=self.user_prepare_id))
            db.session.commit()

    def _validate_on_submit(self):
        self.errors = {}
        if not self.company_name:
            self.errors["company_name"] = "Company name is required."
        else:
            duplicate = Obj.query.filter(
                func.lower(Obj.company_name) == func.lower(self.company_name),
                Obj.id != self.id
            ).first()
            if duplicate:
                self.errors["company_name"] = "Company name already exists."
        return not self.errors
