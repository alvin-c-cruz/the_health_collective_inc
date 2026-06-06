from dataclasses import dataclass

from sqlalchemy import func

from application.blueprints.audit.utils import (
    log_create,
    log_update,
    model_to_dict,
)
from application.blueprints.register.product_type.models import ProductType
from application.extensions import db

from . import app_name
from .admin_models import UserProduct as Preparer
from .models import Product as Obj


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
    product_name: str = ""
    product_type_id: int = None
    product_type_name: str = ""

    user_prepare_id: int = None
    user_prepare: str = ""

    errors = {}

    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors"]:
                continue
            if attribute in ["product_type_id"]:
                setattr(self, attribute, int(getattr(row, attribute)))
                product_type = ProductType.query.get(getattr(row, attribute))
                self.product_type_name = (
                    product_type.product_type_name if product_type else ""
                )
            elif attribute == "product_type_name":
                pass
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
            _dict.pop("product_type_name")

            new_record = Obj(**_dict)
            db.session.add(new_record)
            db.session.flush()

            # Log creation after flush to get ID
            log_create(
                module="product",
                record_id=new_record.id,
                record_identifier=str(new_record),
                new_values=model_to_dict(
                    new_record, ["product_name", "product_type_id"]
                ),
                notes="Product created",
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
                old_values = model_to_dict(record, ["product_name", "product_type_id"])

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
                new_values = model_to_dict(record, ["product_name", "product_type_id"])

                # Log update before commit
                log_update(
                    module="product",
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

            elif attribute in ["product_type_id"]:
                product_type_name = request_form.get("product_type_name")
                product_type = ProductType.query.filter_by(
                    product_type_name=product_type_name
                ).first()
                if product_type:
                    setattr(self, attribute, product_type.id)
                self.product_type_name = product_type_name

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

        if not self.product_name:
            self.errors["product_name"] = "Please type product name."
        else:
            duplicate = Obj.query.filter(
                func.lower(Obj.product_name) == func.lower(self.product_name),
                Obj.id != self.id,
            ).first()
            if duplicate:
                self.errors["product_name"] = "Product name is already used."

        if not self.product_type_name:
            self.errors["product_type_name"] = "Please select product type."
        else:
            product_type = ProductType.query.filter(
                ProductType.product_type_name == self.product_type_name
            ).first()
            if not product_type:
                self.errors["product_type_name"] = (
                    f"{self.product_type_name} does not exists."
                )
            else:
                self.product_type_id = product_type.id

        if not self.errors:
            return True
        return False
