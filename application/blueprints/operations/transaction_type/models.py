from application.extensions import db


class TransactionType(db.Model):
    __tablename__ = "transaction_type"
    id = db.Column(db.Integer, primary_key=True)
    type_code = db.Column(db.String(), unique=True, nullable=False)
    type_name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), default="")
    icon = db.Column(db.String(), default="bi-tag")
    icon_color = db.Column(db.String(), default="ic-blue")
    badge_color = db.Column(db.String(), default="thc-badge-blue")
    active = db.Column(db.Boolean(), default=True)
    sort_order = db.Column(db.Integer(), default=99)

    def __repr__(self):
        return self.type_name
