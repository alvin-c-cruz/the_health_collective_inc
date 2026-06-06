from application.extensions import db

from . import app_name


class UserTransaction(db.Model):
    transaction_id = db.Column(
        db.Integer, db.ForeignKey("transaction.id"), primary_key=True
    )
    transaction = db.relationship("Transaction", backref="user_prepare", lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    user = db.relationship("User", backref=f"{app_name}_prepared", lazy=True)

    def __str__(self):
        return f"UserTransaction(transaction_id={self.transaction_id}, user_id={self.user_id})"

    def __repr__(self):
        return self.user.user_name


class AdminTransaction(db.Model):
    transaction_id = db.Column(
        db.Integer, db.ForeignKey("transaction.id"), primary_key=True
    )
    transaction = db.relationship("Transaction", backref="user_approved", lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    user = db.relationship("User", backref=f"{app_name}_approved", lazy=True)

    def __str__(self):
        return f"AdminTransaction(transaction_id={self.transaction_id}, user_id={self.user_id})"

    def __repr__(self):
        return self.user.user_name
