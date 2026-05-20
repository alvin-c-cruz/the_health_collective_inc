from datetime import date
from application.extensions import db


class ApeBatch(db.Model):
    id = db.Column(db.Integer(), primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company', backref='ape_batches', lazy=True)

    batch_date = db.Column(db.String())
    loa_soa_number = db.Column(db.String(255))
    package_amount = db.Column(db.Float, default=0)
    notes = db.Column(db.String())

    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    creator = db.relationship('User', lazy=True)
    created_at = db.Column(db.String())

    def __str__(self):
        return f"{self.company.company_name} — {self.batch_date}"

    @property
    def transactions(self):
        from application.blueprints.operations.daily_sales.models import Transaction
        return Transaction.query.filter_by(ape_batch_id=self.id).all()

    @property
    def employee_count(self):
        return len(self.transactions)

    @property
    def total_amount(self):
        return sum(
            td.amount
            for t in self.transactions
            for td in t.transaction_details
        )

    @property
    def total_collected(self):
        return sum(col.total_amount for col in self.collections)

    @property
    def outstanding_balance(self):
        return self.total_amount - self.total_collected
