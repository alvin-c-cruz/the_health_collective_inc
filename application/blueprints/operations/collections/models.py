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

    # Status workflow fields (matching Deposit model)
    status = db.Column(db.String(20), default='draft')  # draft | submitted | posted | cancelled

    # Audit trail fields
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    created_at = db.Column(db.String())

    submitted_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    submitted_by = db.relationship("User", foreign_keys=[submitted_by_id])
    submitted_at = db.Column(db.DateTime, nullable=True)

    approved_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    approved_by = db.relationship("User", foreign_keys=[approved_by_id])
    approved_at = db.Column(db.DateTime, nullable=True)

    cancelled_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id])
    cancelled_at = db.Column(db.DateTime, nullable=True)
    cancellation_reason = db.Column(db.String(500), nullable=True)

    updated_at = db.Column(db.DateTime, nullable=True)

    # Legacy field for backwards compatibility (renamed from recorded_by)
    recorded_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    ape_batch_id = db.Column(db.Integer, db.ForeignKey("ape_batch.id"), nullable=True)
    ape_batch    = db.relationship("ApeBatch", backref="collections", lazy=True)

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

    @property
    def formatted_total_amount(self):
        """Alias for formatted_total to match Deposit model"""
        return self.formatted_total


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
