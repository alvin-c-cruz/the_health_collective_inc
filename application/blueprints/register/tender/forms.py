from dataclasses import dataclass

from sqlalchemy import func

from application.blueprints.audit.utils import (
    log_create,
    log_update,
    model_to_dict,
)
from application.extensions import db

from . import app_name
from .admin_models import UserTender as Preparer
from .models import Tender as Obj


def get_attributes(object):
    attributes = [x for x in dir(object) if (not x.startswith("_"))]
    exceptions = (
        "user_prepare_id",
        "user_prepare",
        "errors",
        "active",
        "details",
        "locked",
        app_name,
    )
    for i in exceptions:
        try:
            attributes.remove(i)
        except ValueError:
            pass
    return attributes


def get_attributes_as_dict(object):
    attributes = get_attributes(object)
    return {attribute: getattr(object, attribute) for attribute in attributes}


@dataclass
class Form:
    id: int = None
    tender_name: str = ""
    symbol: str = ""
    transaction_types: str = ""
    sort_order: int = 0
    report_static: bool = False
    is_receivable: bool = False

    user_prepare_id: int = None
    user_prepare: str = ""

    errors = {}

    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors"]:
                continue
            value = getattr(row, attribute)
            if value is None:
                setattr(self, attribute, "")
            else:
                setattr(self, attribute, value)

    def _save(self):
        if self.id is None:
            # Add a new record
            _dict = get_attributes_as_dict(self)
            if "locked" in _dict:
                _dict.pop("locked")

            new_record = Obj(**_dict)
            db.session.add(new_record)
            db.session.flush()

            # Log creation after flush to get ID
            log_create(
                module="tender",
                record_id=new_record.id,
                record_identifier=str(new_record),
                new_values=model_to_dict(
                    new_record,
                    [
                        "tender_name",
                        "symbol",
                        "transaction_types",
                        "sort_order",
                        "report_static",
                        "is_receivable",
                    ],
                ),
                notes="Tender created",
            )

            db.session.commit()

            data = {f"{app_name}_id": new_record.id, "user_id": self.user_prepare_id}

            preparer = Preparer(**data)

            db.session.add(preparer)
            db.session.commit()

        else:
            # Update an existing record
            record = Obj.query.get(self.id)
            if record:
                # Capture old values before update
                old_values = model_to_dict(
                    record,
                    [
                        "tender_name",
                        "symbol",
                        "transaction_types",
                        "sort_order",
                        "report_static",
                        "is_receivable",
                    ],
                )

                data = {f"{app_name}_id": self.id}

                preparer = Preparer.query.filter_by(**data).first()
                if preparer:
                    preparer.user_id = self.user_prepare_id
                else:
                    data["user_id"] = self.user_prepare_id
                    preparer = Preparer(**data)
                    db.session.add(preparer)

                for attribute in get_attributes(self):
                    if attribute == "id":
                        continue
                    setattr(record, attribute, getattr(self, attribute))

                # Capture new values after update
                new_values = model_to_dict(
                    record,
                    [
                        "tender_name",
                        "symbol",
                        "transaction_types",
                        "sort_order",
                        "report_static",
                        "is_receivable",
                    ],
                )

                # Log update before commit
                log_update(
                    module="tender",
                    record_id=record.id,
                    record_identifier=str(record),
                    old_values=old_values,
                    new_values=new_values,
                )

        db.session.commit()

    def _post(self, request_form, current_user_id):
        for attribute in get_attributes(self):
            if attribute == "id":
                value = request_form.get("record_id")
                if value:
                    self.id = int(value)
            elif attribute == "transaction_types":
                types = request_form.getlist("transaction_types")
                self.transaction_types = ",".join(types)
            elif attribute == "sort_order":
                raw = request_form.get("sort_order", "0")
                try:
                    self.sort_order = int(raw)
                except (ValueError, TypeError):
                    self.sort_order = 0
            elif attribute == "report_static":
                self.report_static = "report_static" in request_form
            elif attribute == "is_receivable":
                self.is_receivable = "is_receivable" in request_form
            elif attribute == "tender_name":
                self.tender_name = (request_form.get("tender_name") or "").strip()
            elif attribute in ("submitted", "cancelled"):
                continue
            else:
                try:
                    setattr(
                        self, attribute, request_form.get(attribute).upper()
                    )
                except:
                    setattr(self, attribute, request_form.get(attribute))

        self.user_prepare_id = current_user_id

    def _validate_on_submit(self):
        self.errors = {}

        if not self.tender_name:
            self.errors["tender_name"] = "Please type tender name."
        else:
            duplicate = Obj.query.filter(
                func.lower(Obj.tender_name) == func.lower(self.tender_name),
                Obj.id != self.id,
            ).first()
            if duplicate:
                self.errors["tender_name"] = "Tender name is already used."

        if not self.errors:
            return True
        return False
