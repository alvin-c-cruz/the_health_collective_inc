from dataclasses import dataclass

from sqlalchemy import func

from application.blueprints.audit.utils import (
    log_create,
    log_update,
    model_to_dict,
)
from application.blueprints.register.sex.models import Sex
from application.extensions import db

from . import app_name
from .admin_models import UserCustomer as Preparer
from .models import Customer as Obj


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
        "get_formatted_name",
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
    customer_name: str = ""  # Legacy field for backwards compatibility
    last_name: str = ""
    first_name: str = ""
    middle_name: str = ""
    birthday: str = ""
    sex_id: int = None
    sex_name: str = ""
    tin: str = ""
    address: str = ""
    business_style: str = ""
    salesman: str = ""

    user_prepare_id: int = None
    user_prepare: str = ""

    errors = {}

    def get_formatted_name(self):
        """Returns formatted name: Last Name, First Name Middle Name"""
        if self.last_name or self.first_name:
            parts = []
            if self.last_name:
                parts.append(self.last_name)
            name_parts = []
            if self.first_name:
                name_parts.append(self.first_name)
            if self.middle_name:
                name_parts.append(self.middle_name)
            if name_parts:
                parts.append(" ".join(name_parts))
            return ", ".join(parts) if len(parts) > 1 else parts[0] if parts else ""
        return self.customer_name or ""

    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors", "sex_name"]:
                continue
            if attribute in ["sex_id"]:
                sex = Sex.query.get(row.sex_id)
                setattr(self, attribute, sex.id)
                self.sex_name = sex.sex_name
            else:
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
            _dict.pop("sex_name")

            new_record = Obj(**_dict)
            db.session.add(new_record)
            db.session.flush()

            # Log creation after flush to get ID
            log_create(
                module="customer",
                record_id=new_record.id,
                record_identifier=str(new_record),
                new_values=model_to_dict(
                    new_record,
                    [
                        "last_name",
                        "first_name",
                        "middle_name",
                        "birthday",
                        "sex_id",
                        "tin",
                        "address",
                        "business_style",
                        "salesman",
                    ],
                ),
                notes="Customer created",
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
                        "last_name",
                        "first_name",
                        "middle_name",
                        "birthday",
                        "sex_id",
                        "tin",
                        "address",
                        "business_style",
                        "salesman",
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
                        "last_name",
                        "first_name",
                        "middle_name",
                        "birthday",
                        "sex_id",
                        "tin",
                        "address",
                        "business_style",
                        "salesman",
                    ],
                )

                # Log update before commit
                log_update(
                    module="customer",
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
            elif attribute in ("submitted", "cancelled"):
                continue
            elif attribute in ["sex_name"]:
                sex_name = request_form.get("sex_name")
                sex = Sex.query.filter_by(sex_name=sex_name).first()
                if sex:
                    self.sex_id = sex.id
                self.sex_name = sex_name
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

        # Require at least last name or first name
        if not self.last_name and not self.first_name:
            self.errors["last_name"] = "Please enter at least Last Name or First Name."
            self.errors["first_name"] = "Please enter at least Last Name or First Name."
        else:
            # Check for duplicate based on full name combination
            duplicate = Obj.query.filter(
                func.lower(Obj.last_name) == func.lower(self.last_name),
                func.lower(Obj.first_name) == func.lower(self.first_name),
                func.lower(Obj.middle_name) == func.lower(self.middle_name),
                Obj.id != self.id,
            ).first()
            if duplicate:
                self.errors["last_name"] = "A patient with this name already exists."

        if not self.sex_name:
            self.errors["sex_name"] = "Please type sex."
        else:
            sex = Sex.query.filter(Sex.sex_name == self.sex_name).first()
            if not sex:
                self.errors["sex_name"] = f"{self.sex_name} does not exist."

        if not self.errors:
            return True
        return False
