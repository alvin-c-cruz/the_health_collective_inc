from application.extensions import db, short_date


class Collection(db.Model):
    __tablename__ = "collection"

    id              = db.Column(db.Integer, primary_key=True)
    collection_date = db.Column(db.String(), nullable=False)
    tender_id       = db.Column(db.Integer, db.ForeignKey("tender.id"), nullable=False)
    tender          = db.relationship("Tender", lazy=True)
    bank_account_id = db.Column(db.Integer, db.ForeignKey("bank_account.id"), nullable=True)
    bank_account    = db.relationship("BankAccount", lazy=True)
    reference       = db.Column(db.String())
    notes           = db.Column(db.String())
    recorded_by     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_at      = db.Column(db.String())

    details = db.relationship("CollectionDetail", backref="collection", lazy=True,
                              cascade="all, delete-orphan")

    @property
    def total_amount(self):
        return sum(d.amount_applied for d in self.details)

    @property
    def formatted_collection_date(self):
        return short_date(self.collection_date) if self.collection_date else ""

    @property
    def formatted_total(self):
        return "{:,.2f}".format(self.total_amount)


class CollectionDetail(db.Model):
    __tablename__ = "collection_detail"

    id                    = db.Column(db.Integer, primary_key=True)
    collection_id         = db.Column(db.Integer, db.ForeignKey("collection.id"), nullable=False)
    transaction_tender_id = db.Column(db.Integer, db.ForeignKey("transaction_tender.id"), nullable=False)
    transaction_tender    = db.relationship("TransactionTender", lazy=True)
    amount_applied        = db.Column(db.Float, default=0)

    @property
    def formatted_amount(self):
        return "{:,.2f}".format(self.amount_applied)
