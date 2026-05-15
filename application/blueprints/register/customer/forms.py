from dataclasses import dataclass
from sqlalchemy import func
from application.blueprints.register.sex.models import Sex
from application.extensions import db
from .models import Customer as Obj
from .admin_models import UserCustomer as Preparer
from . import app_name

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
    customer_name: str = ""
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
       
    def _populate(self, row):
        for attribute in get_attributes(self):
            if attribute in ["errors", "sex_name"]:
                continue
            elif attribute in ["sex_id"]:
                sex = Sex.query.get(getattr(row, "sex_id"))
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
            if "locked" in _dict: _dict.pop("locked")
            _dict.pop("sex_name")

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
            elif attribute in ("submitted", "cancelled"):
                continue
            elif attribute in ["sex_name"]:
                sex_name = request_form.get('sex_name')
                sex = Sex.query.filter_by(
                    sex_name=sex_name
                    ).first()
                if sex:
                    setattr(self, "sex_id", sex.id)
                self.sex_name = sex_name
            else:
                try:
                    setattr(self, attribute, getattr(request_form, "get")(attribute).upper())
                except:
                    setattr(self, attribute, getattr(request_form, "get")(attribute)) 
            
            self.user_prepare_id = current_user_id

    def _validate_on_submit(self):
        self.errors = {}

        if not self.customer_name:
            self.errors["customer_name"] = "Please type customer name."
        else:
            duplicate = Obj.query.filter(
                func.lower(
                    Obj.customer_name
                    ) == func.lower(self.customer_name), 
                    Obj.id != self.id
                    ).first()
            if duplicate:
                self.errors["customer_name"] = "Customer name is already used."               

        if not self.sex_name:
            self.errors["sex_name"] = "Please type sex."
        else:
            sex = Sex.query.filter(Sex.sex_name == self.sex_name).first()
            if not sex:
                self.errors["sex_name"] = f"{self.sex_name} does not exist."


        if not self.errors:
            return True     
        else:
            return False   
    