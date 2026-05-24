"""
Audit Trail Models for Transaction History Tracking

This module provides comprehensive audit logging for all changes to transactions,
including field-level change tracking, user attribution, and timestamps.
"""
import json
from datetime import datetime
from application.extensions import db


class AuditLog(db.Model):
    """
    Comprehensive audit log for tracking all changes to records.

    Tracks:
    - Who made the change (user_id)
    - When the change was made (timestamp)
    - What record was changed (record_type, record_id)
    - What action was performed (created, updated, deleted, submitted, approved, cancelled)
    - What fields changed (old_values, new_values)
    - Why the change was made (reason, if applicable)
    """
    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)

    # Record identification
    record_type = db.Column(db.String(50), nullable=False)  # 'transaction', 'deposit', 'customer', etc.
    record_id = db.Column(db.Integer, nullable=False)  # ID of the record

    # Action performed
    action = db.Column(db.String(50), nullable=False)  # 'created', 'updated', 'deleted', 'submitted', 'approved', 'cancelled', 'returned_to_draft'

    # Change details - JSON encoded
    _old_values = db.Column('old_values', db.Text)  # Previous field values
    _new_values = db.Column('new_values', db.Text)  # New field values
    _changed_fields = db.Column('changed_fields', db.Text)  # List of field names that changed

    # Reason/notes for the change
    reason = db.Column(db.String(500))
    notes = db.Column(db.Text)

    # User who made the change
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='audit_logs')

    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # IP address (optional, for security)
    ip_address = db.Column(db.String(45))

    # Additional metadata
    extra_metadata = db.Column(db.Text)  # JSON for extra context

    @property
    def old_values(self):
        """Deserialize old values from JSON"""
        return json.loads(self._old_values) if self._old_values else {}

    @old_values.setter
    def old_values(self, val):
        """Serialize old values to JSON"""
        self._old_values = json.dumps(val) if val else None

    @property
    def new_values(self):
        """Deserialize new values from JSON"""
        return json.loads(self._new_values) if self._new_values else {}

    @new_values.setter
    def new_values(self, val):
        """Serialize new values to JSON"""
        self._new_values = json.dumps(val) if val else None

    @property
    def changed_fields(self):
        """Deserialize changed fields list from JSON"""
        return json.loads(self._changed_fields) if self._changed_fields else []

    @changed_fields.setter
    def changed_fields(self, val):
        """Serialize changed fields list to JSON"""
        self._changed_fields = json.dumps(val) if val else None

    @property
    def metadata_dict(self):
        """Deserialize metadata from JSON"""
        return json.loads(self.extra_metadata) if self.extra_metadata else {}

    @metadata_dict.setter
    def metadata_dict(self, val):
        """Serialize metadata to JSON"""
        self.extra_metadata = json.dumps(val) if val else None

    def __repr__(self):
        return f'<AuditLog {self.action} {self.record_type}#{self.record_id} by user#{self.user_id} at {self.created_at}>'

    @property
    def formatted_timestamp(self):
        """Format timestamp for display"""
        if self.created_at:
            return self.created_at.strftime('%Y-%m-%d %I:%M:%S %p')
        return 'N/A'

    @property
    def summary(self):
        """Generate a human-readable summary of the change"""
        user_name = self.user.user_name if self.user else 'Unknown'

        if self.action == 'created':
            return f"{user_name} created this record"
        elif self.action == 'updated':
            if self.changed_fields:
                fields = ', '.join(self.changed_fields)
                return f"{user_name} updated: {fields}"
            return f"{user_name} updated this record"
        elif self.action == 'deleted':
            return f"{user_name} deleted this record"
        elif self.action == 'submitted':
            return f"{user_name} submitted for approval"
        elif self.action == 'approved':
            return f"{user_name} approved this record"
        elif self.action == 'cancelled':
            reason_text = f" - {self.reason}" if self.reason else ""
            return f"{user_name} cancelled this record{reason_text}"
        elif self.action == 'returned_to_draft':
            reason_text = f" - {self.reason}" if self.reason else ""
            return f"{user_name} returned to draft{reason_text}"
        elif self.action == 'cancellation_requested':
            return f"{user_name} requested cancellation"
        elif self.action == 'cancellation_approved':
            return f"{user_name} approved cancellation request"
        elif self.action == 'cancellation_rejected':
            return f"{user_name} rejected cancellation request"
        else:
            return f"{user_name} performed action: {self.action}"
