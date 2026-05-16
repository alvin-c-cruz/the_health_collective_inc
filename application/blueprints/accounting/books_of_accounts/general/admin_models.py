from application.extensions import db

from . import app_name, app_label

class UserGeneral(db.Model):
    general_id = db.Column(db.Integer, db.ForeignKey(f'{app_name}.id'), primary_key=True)
    general = db.relationship(app_label.replace(" ", ""), backref='user_prepare', lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', backref=f'{app_name}_prepared', lazy=True)

    def __str__(self):
        data = {
            "user_id": self.user_id,
            f"{app_name}_id": getattr(self, f"{app_name}_id")
        }
        
        return data

    def __repr__(self):
        return self.user.user_name


class AdminGeneral(db.Model):
    general_id = db.Column(db.Integer, db.ForeignKey(f'{app_name}.id'), primary_key=True)
    general = db.relationship(app_label.replace(" ", ""), backref='user_approved', lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', backref=f'{app_name}_approved', lazy=True)

    def __str__(self):
        return self.user.user_name

    def __repr__(self):
        return self.user.user_name
