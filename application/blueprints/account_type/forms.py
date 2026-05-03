from dataclasses import dataclass
from sqlalchemy import func
from application.extensions import db
from .models import AccountType as Obj
from .admin_models import UserAccountType as Preparer
from .admin_models import AdminAccountType as Approver
from . import app_name
from datetime import datetime

from .. account_class import AccountClass



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
    account_type_name: str = ""
    account_class_name: str = ""
    account_class_id: int = None
    priority: str = ""
    
    user_prepare_id: int = None
    user_prepare: str = ""

    errors = {}
       
    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors", "account_class_name"]:
                continue
            else:
                attribute_value = getattr(row, attribute)
                setattr(self, attribute, attribute_value)
                if attribute == "account_class_id":
                    account_class = AccountClass.query.filter_by(id=attribute_value).first()
                    self.account_class_name = account_class.account_class_name

    def _save(self):
        if self.id is None:
            # Add a new record
            _dict = get_attributes_as_dict(self)
            if "locked" in _dict: _dict.pop("locked")
            
            _dict.pop("account_class_name")
            
            new_record = Obj(
                **_dict
                )
            db.session.add(new_record)
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
                                                    
        db.session.commit()
   

    def _post(self, request_form, current_user_id):
        for attribute in get_attributes(self):
            if attribute == "id":
                value = getattr(request_form, "get")("record_id")
                if value:
                    setattr(self, "id", int(value))
            elif attribute == "account_class_name":
                attribute_value = getattr(request_form, "get")("account_class_name")
                account_class = AccountClass.query.filter(AccountClass.account_class_name==attribute_value).first()
                print(account_class)
                self.account_class_name = account_class.account_class_name
                self.account_class_id = account_class.id
                
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

        if not self.account_type_name:
            self.errors["account_type_name"] = "Please type description."
        else:
            duplicate = Obj.query.filter(
                func.lower(
                    Obj.account_type_name
                    ) == func.lower(self.account_type_name), 
                    Obj.id != self.id
                    ).first()
            if duplicate:
                self.errors["account_type_name"] = "Account type is already used."             
    
        if not self.account_class_name:
            self.errors["account_class_name"] = "Please type account classification."
        else:
            existing = AccountClass.query.filter(
                func.lower(
                    AccountClass.account_class_name
                    ) == func.lower(self.account_class_name)
                    ).first()
            if not existing:
                self.errors["account_class_name"] = "Account Classification is invalid."        

        if not self.errors:
            return True     
        else:
            return False   
    