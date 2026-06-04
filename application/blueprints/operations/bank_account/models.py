from application.extensions import db


class BankAccount(db.Model):
    id             = db.Column(db.Integer, primary_key=True)
    bank_name      = db.Column(db.String(255), nullable=False)
    account_name   = db.Column(db.String(255))
    account_number = db.Column(db.String(100))
    display_name   = db.Column(db.String(500))  # Custom display name for dropdowns
    notes          = db.Column(db.String())
    active         = db.Column(db.Boolean, default=True)

    def __str__(self):
        # Use custom display_name if set, otherwise fallback to default format
        if self.display_name:
            return self.display_name
        return f"{self.bank_name} — {self.account_number}"
