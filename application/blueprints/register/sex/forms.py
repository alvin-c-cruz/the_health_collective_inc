from dataclasses import dataclass
from sqlalchemy import func
from application.extensions import db
from .models import Sex as Obj
from .admin_models import UserSex as Preparer
from . import app_name
from application.blueprints.audit.utils import (
    log_create, log_update, log_delete,
    model_to_dict, get_record_identifier
)

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
    return {
        attribute: getattr(object, attribute)
        for attribute in attributes
    }
    
    
@dataclass
class Form:
    id: int = None
    sex_name: str = ""
    
    user_prepare_id: int = None
    user_prepare: str = ""

    errors = {}
       
    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors"]:
                continue
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
            if "locked" in _dict: _dict.pop("locked")

            new_record = Obj(
                **_dict
                )
            db.session.add(new_record)
            db.session.flush()

            # Log creation after flush to get ID
            log_create(
                module='sex',
                record_id=new_record.id,
                record_identifier=str(new_record),
                new_values=model_to_dict(new_record, ['sex_name']),
                notes='Sex created'
            )

            db.session.commit()

            data = {
                f"{app_name}_id": new_record.id,
                "user_id": self.user_prepare_id
            }

            preparer = Preparer(**data)

            db.session.add(preparer)
            db.session.commit()

        else:
            # Update an existing record
            record = Obj.query.get(self.id)
            if record:
                # Capture old values before update
                old_values = model_to_dict(record, ['sex_name'])

                data = {
                    f"{app_name}_id": self.id
                }

                preparer = Preparer.query.filter_by(**data).first()
                if preparer:
                    preparer.user_id = self.user_prepare_id
                else:
                    data[f"user_id"] = self.user_prepare_id
                    preparer = Preparer(**data)
                    db.session.add(preparer)

                for attribute in get_attributes(self):
                    if attribute == "id": continue
                    setattr(record, attribute, getattr(self, attribute))

                # Capture new values after update
                new_values = model_to_dict(record, ['sex_name'])

                # Log update before commit
                log_update(
                    module='sex',
                    record_id=record.id,
                    record_identifier=str(record),
                    old_values=old_values,
                    new_values=new_values
                )

        db.session.commit()
   

    def _post(self, request_form, current_user_id):
        for attribute in get_attributes(self):
            if attribute == "id":
                value = getattr(request_form, "get")("record_id")
                if value:
                    setattr(self, "id", int(value))
            elif attribute in ("submitted", "cancelled"):
                continue
            else:
                try:
                    setattr(self, attribute, getattr(request_form, "get")(attribute).upper())
                except:
                    setattr(self, attribute, getattr(request_form, "get")(attribute)) 
            
            self.user_prepare_id = current_user_id

    def _validate_on_submit(self):
        self.errors = {}

        if not self.sex_name:
            self.errors["sex_name"] = "Please type description."
        else:
            duplicate = Obj.query.filter(
                func.lower(
                    Obj.sex_name
                    ) == func.lower(self.sex_name), 
                    Obj.id != self.id
                    ).first()
            if duplicate:
                self.errors["sex_name"] = "Sex is already used."               

        if not self.errors:
            return True     
        else:
            return False   
    