import json
from datetime import datetime
from application.extensions import db


class ChangeRequest(db.Model):
    """
    Model for tracking change requests on transactions and deposits.

    Workflow:
    - Staff requests to modify a submitted/posted transaction or deposit
    - Admin reviews and approves/rejects the request
    - If approved, record is updated and requires re-approval (if applicable)
    """
    __tablename__ = 'change_request'

    id = db.Column(db.Integer, primary_key=True)

    # Type of record being changed: 'transaction' or 'deposit'
    record_type = db.Column(db.String(20), nullable=False)

    # ID of the record being modified (transaction_id or deposit_id)
    record_id = db.Column(db.Integer, nullable=False)

    # Legacy field for backwards compatibility with existing transaction change requests
    transaction_id = db.Column(db.Integer, db.ForeignKey('transaction.id'), nullable=True)
    transaction = db.relationship('Transaction', backref='change_requests', lazy=True)

    # JSON-encoded old and new values
    _old_values = db.Column('old_values', db.Text)
    _new_values = db.Column('new_values', db.Text)

    # Action requested: 'modification' or 'cancellation'
    request_action = db.Column(db.String(20), default='modification')

    # Reason for the change request
    reason = db.Column(db.String(500), nullable=False)

    # Status: pending | approved | rejected | direct (superuser direct edit)
    status = db.Column(db.String(20), default='pending')

    # Audit trail - who requested
    requested_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    requested_by = db.relationship('User', foreign_keys=[requested_by_id], backref='change_requests_made')
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Audit trail - who reviewed
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id], backref='change_requests_reviewed')
    reviewed_at = db.Column(db.DateTime, nullable=True)
    review_notes = db.Column(db.String(500))

    @property
    def old_values(self):
        """Deserialize old values from JSON"""
        return json.loads(self._old_values) if self._old_values else {}

    @old_values.setter
    def old_values(self, val):
        """Serialize old values to JSON"""
        self._old_values = json.dumps(val)

    @property
    def new_values(self):
        """Deserialize new values from JSON"""
        return json.loads(self._new_values) if self._new_values else {}

    @new_values.setter
    def new_values(self, val):
        """Serialize new values to JSON"""
        self._new_values = json.dumps(val)

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_rejected(self):
        return self.status == 'rejected'

    @property
    def is_direct(self):
        return self.status == 'direct'

    @property
    def is_cancellation(self):
        return self.request_action == 'cancellation'

    @property
    def is_modification(self):
        return self.request_action == 'modification'

    @property
    def deposit(self):
        """Get the deposit record if record_type is 'deposit'"""
        if self.record_type == 'deposit':
            from .models import Deposit
            return Deposit.query.get(self.record_id)
        return None

    @property
    def collection(self):
        """Get the collection record if record_type is 'collection'"""
        if self.record_type == 'collection':
            from ..collections.models import Collection
            return Collection.query.get(self.record_id)
        return None

    @property
    def record(self):
        """Get the actual record (transaction, deposit, or collection) being modified"""
        if self.record_type == 'transaction':
            return self.transaction
        elif self.record_type == 'deposit':
            return self.deposit
        elif self.record_type == 'collection':
            return self.collection
        return None
