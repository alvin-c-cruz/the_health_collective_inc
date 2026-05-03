from application.extensions import db

from . import app_name, app_label

class UserMeasure(db.Model):
    measure_id = db.Column(db.Integer, db.ForeignKey(f'{app_name}.id'), primary_key=True)
    measure = db.relationship(app_label, backref='user_prepare', lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', backref=f'{app_name}_prepared', lazy=True)

    def __str__(self):
        return f"user={self.user_id}; measure_id={self.measure_id}"

    def __repr__(self):
        return self.user.user_name


class AdminMeasure(db.Model):
    measure_id = db.Column(db.Integer, db.ForeignKey(f'{app_name}.id'), primary_key=True)
    measure = db.relationship(app_label, backref='user_approved', lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', backref=f'{app_name}_approved', lazy=True)

    def __str__(self):
        return self.user.user_name

    def __repr__(self):
        return self.user.user_name
