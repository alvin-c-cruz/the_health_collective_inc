"""
Centralized Audit Trail Models

Following the CAS pattern with improvements based on critical review:
- Object-level JSON tracking (not field-level)
- Denormalized user fields for safety (survives user deletion)
- Philippine timezone awareness
- IP address and user agent tracking
"""
import json
from datetime import datetime
from application.extensions import db
from zoneinfo import ZoneInfo

# Philippine timezone
_PH = ZoneInfo('Asia/Manila')


def ph_now():
    """Return current datetime in Philippine timezone (UTC+8)"""
    return datetime.now(_PH)


class AuditLog(db.Model):
    """
    Centralized audit log for tracking all changes across all modules.

    Tracks:
    - Who: user_id, username, full_name (denormalized for safety)
    - What: module, action, record_id, record_identifier
    - When: timestamp (Philippine time)
    - Where/How: ip_address, user_agent
    - Changes: old_values, new_values (JSON)
    """
    __tablename__ = 'audit_logs'

    # Primary key
    id = db.Column(db.Integer, primary_key=True)

    # Record identification
    module = db.Column(db.String(50), nullable=False, index=True)  # 'customer', 'transaction', 'journal', etc.
    action = db.Column(db.String(20), nullable=False, index=True)  # 'created', 'updated', 'deleted', 'submitted', 'approved', etc.
    record_id = db.Column(db.Integer)  # ID of the affected record
    record_identifier = db.Column(db.String(200))  # Human-readable identifier (e.g., "CUST-001 - ABC Corp")

    # Who made the change (with denormalization for safety)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    username = db.Column(db.String(80))  # Denormalized - preserved even if user deleted
    full_name = db.Column(db.String(200))  # Denormalized - preserved even if user deleted
    user = db.relationship('User', backref='audit_logs_new', foreign_keys=[user_id])

    # When the change was made (Philippine time)
    timestamp = db.Column(db.DateTime, default=ph_now, nullable=False, index=True)

    # What changed (JSON storage for flexibility)
    _old_values = db.Column('old_values', db.Text)  # JSON: previous field values
    _new_values = db.Column('new_values', db.Text)  # JSON: new field values

    # Where/How the change was made
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(500))  # Browser/client info

    # Additional context
    reason = db.Column(db.String(500))  # Reason for change (optional)
    notes = db.Column(db.Text)  # Additional notes (optional)

    # JSON property accessors
    @property
    def old_values(self):
        """Deserialize old values from JSON"""
        return json.loads(self._old_values) if self._old_values else {}

    @old_values.setter
    def old_values(self, val):
        """Serialize old values to JSON"""
        self._old_values = json.dumps(val, default=str) if val else None

    @property
    def new_values(self):
        """Deserialize new values from JSON"""
        return json.loads(self._new_values) if self._new_values else {}

    @new_values.setter
    def new_values(self, val):
        """Serialize new values to JSON"""
        self._new_values = json.dumps(val, default=str) if val else None

    @property
    def changed_fields(self):
        """Get list of fields that changed (derived from old/new values)"""
        if not self.old_values or not self.new_values:
            return []

        old = self.old_values
        new = self.new_values

        # Find fields that exist in both and have different values
        changed = []
        for key in set(old.keys()) | set(new.keys()):
            old_val = old.get(key)
            new_val = new.get(key)
            if old_val != new_val:
                changed.append(key)

        return changed

    @property
    def formatted_timestamp(self):
        """Format timestamp for display"""
        if self.timestamp:
            return self.timestamp.strftime('%Y-%m-%d %I:%M:%S %p')
        return 'N/A'

    @property
    def summary(self):
        """Generate human-readable summary of the change"""
        # Use denormalized username/full_name if user is deleted
        if self.user:
            user_display = self.user.user_name
        elif self.username:
            user_display = self.username
        else:
            user_display = 'Unknown'

        action_text = self.action.replace('_', ' ').title()

        if self.action == 'created':
            return f"{user_display} created this record"
        elif self.action == 'updated':
            if self.changed_fields:
                fields = ', '.join(self.changed_fields)
                return f"{user_display} updated: {fields}"
            return f"{user_display} updated this record"
        elif self.action == 'deleted':
            return f"{user_display} deleted this record"
        elif self.reason:
            return f"{user_display} {action_text}: {self.reason}"
        else:
            return f"{user_display} {action_text}"

    def __repr__(self):
        return f'<AuditLog {self.action} {self.module}#{self.record_id} by {self.username} at {self.timestamp}>'


class LoginHistory(db.Model):
    """
    Login history tracking for security and compliance.

    Tracks both successful and failed login attempts with context.
    """
    __tablename__ = 'login_history'

    id = db.Column(db.Integer, primary_key=True)

    # User information (denormalized for safety)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), index=True)
    username = db.Column(db.String(80), nullable=False)  # Preserved even if user deleted
    full_name = db.Column(db.String(200))
    user = db.relationship('User', backref='login_history', foreign_keys=[user_id])

    # Login details
    login_time = db.Column(db.DateTime, default=ph_now, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, index=True)  # 'success' or 'failed'
    failure_reason = db.Column(db.String(200))  # Why login failed (if applicable)

    # Where/How
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))

    @property
    def formatted_login_time(self):
        """Format login time for display"""
        if self.login_time:
            return self.login_time.strftime('%Y-%m-%d %I:%M:%S %p')
        return 'N/A'

    def __repr__(self):
        return f'<LoginHistory {self.status} {self.username} at {self.login_time}>'
