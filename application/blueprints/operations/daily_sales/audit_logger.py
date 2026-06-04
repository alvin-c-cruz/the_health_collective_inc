"""
Audit Logging Helper Functions

Provides utilities for logging changes to transactions and other records.
"""
from datetime import datetime
from flask import request
from flask_login import current_user
from application.extensions import db
from .audit_models import AuditLog


def get_model_snapshot(instance, exclude_fields=None):
    """
    Create a snapshot of a model instance's current state.

    Args:
        instance: SQLAlchemy model instance
        exclude_fields: List of field names to exclude from snapshot

    Returns:
        dict: Field name -> value mapping
    """
    if exclude_fields is None:
        exclude_fields = ['_sa_instance_state', 'updated_at', 'created_at']

    snapshot = {}
    for column in instance.__table__.columns:
        field_name = column.name
        if field_name not in exclude_fields:
            value = getattr(instance, field_name, None)
            # Convert datetime to string for JSON serialization
            if isinstance(value, datetime):
                value = value.isoformat()
            snapshot[field_name] = value

    return snapshot


def get_changed_fields(old_values, new_values):
    """
    Compare old and new values to identify changed fields.

    Args:
        old_values: dict of old field values
        new_values: dict of new field values

    Returns:
        list: Names of fields that changed
    """
    changed = []
    all_fields = set(old_values.keys()) | set(new_values.keys())

    for field in all_fields:
        old_val = old_values.get(field)
        new_val = new_values.get(field)

        # Normalize empty values: treat None, '', and empty strings as equivalent
        # This prevents meaningless audit logs like "None → ''" or "'' → None"
        old_val_normalized = old_val if old_val not in (None, '', ' ') else None
        new_val_normalized = new_val if new_val not in (None, '', ' ') else None

        # Only log if there's a meaningful change
        if old_val_normalized != new_val_normalized:
            changed.append(field)

    return changed


def log_audit(record_type, record_id, action, old_values=None, new_values=None,
              reason=None, notes=None, user=None, metadata=None):
    """
    Create an audit log entry.

    Args:
        record_type: Type of record ('transaction', 'deposit', etc.)
        record_id: ID of the record
        action: Action performed ('created', 'updated', 'deleted', etc.)
        old_values: dict of old field values (optional)
        new_values: dict of new field values (optional)
        reason: Reason for the change (optional)
        notes: Additional notes (optional)
        user: User who made the change (defaults to current_user)
        metadata: Additional metadata dict (optional)

    Returns:
        AuditLog: Created audit log entry
    """
    if user is None:
        user = current_user

    # Get user ID - handle both authenticated and system users
    try:
        user_id = user.id if user and hasattr(user, 'id') else None
    except:
        user_id = None

    # If no user ID, don't create audit log (system operations)
    if user_id is None:
        return None

    # Calculate changed fields if both old and new values provided
    changed_fields = []
    if old_values and new_values:
        changed_fields = get_changed_fields(old_values, new_values)

    # Get IP address from request if available
    # Handle proxy headers (e.g., from PythonAnywhere, nginx, Apache)
    ip_address = None
    try:
        if request:
            # Try to get real client IP from proxy headers first
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)

            # X-Forwarded-For may contain multiple IPs (client, proxy1, proxy2, ...)
            # The first IP is the actual client IP
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()

            # Fallback to X-Real-IP if X-Forwarded-For is not set
            if not ip_address:
                ip_address = request.headers.get('X-Real-IP', request.remote_addr)
    except:
        pass

    # Create audit log entry
    audit_log = AuditLog(
        record_type=record_type,
        record_id=record_id,
        action=action,
        old_values=old_values,
        new_values=new_values,
        changed_fields=changed_fields,
        reason=reason,
        notes=notes,
        user_id=user_id,
        created_at=datetime.utcnow(),
        ip_address=ip_address
    )

    if metadata:
        audit_log.metadata_dict = metadata

    db.session.add(audit_log)
    # Note: Caller is responsible for committing the transaction

    return audit_log


def log_create(record_type, instance, user=None, notes=None):
    """
    Log creation of a new record.

    Args:
        record_type: Type of record ('transaction', 'deposit', etc.)
        instance: The created model instance
        user: User who created the record (defaults to current_user)
        notes: Additional notes (optional)

    Returns:
        AuditLog: Created audit log entry
    """
    new_values = get_model_snapshot(instance)

    return log_audit(
        record_type=record_type,
        record_id=instance.id,
        action='created',
        new_values=new_values,
        notes=notes,
        user=user
    )


def log_update(record_type, instance, old_snapshot, user=None, reason=None, notes=None):
    """
    Log update to an existing record.

    Args:
        record_type: Type of record ('transaction', 'deposit', etc.)
        instance: The updated model instance (with new values)
        old_snapshot: dict of old field values (before update)
        user: User who updated the record (defaults to current_user)
        reason: Reason for the update (optional)
        notes: Additional notes (optional)

    Returns:
        AuditLog: Created audit log entry
    """
    new_values = get_model_snapshot(instance)

    return log_audit(
        record_type=record_type,
        record_id=instance.id,
        action='updated',
        old_values=old_snapshot,
        new_values=new_values,
        reason=reason,
        notes=notes,
        user=user
    )


def log_delete(record_type, instance, user=None, reason=None, notes=None):
    """
    Log deletion of a record.

    Args:
        record_type: Type of record ('transaction', 'deposit', etc.)
        instance: The model instance being deleted
        user: User who deleted the record (defaults to current_user)
        reason: Reason for deletion (optional)
        notes: Additional notes (optional)

    Returns:
        AuditLog: Created audit log entry
    """
    old_values = get_model_snapshot(instance)

    return log_audit(
        record_type=record_type,
        record_id=instance.id,
        action='deleted',
        old_values=old_values,
        reason=reason,
        notes=notes,
        user=user
    )


def log_status_change(record_type, instance, action, user=None, reason=None, notes=None):
    """
    Log status change (submitted, approved, cancelled, etc.)

    Args:
        record_type: Type of record ('transaction', 'deposit', etc.)
        instance: The model instance
        action: The status action ('submitted', 'approved', 'cancelled', etc.)
        user: User who changed the status (defaults to current_user)
        reason: Reason for status change (optional)
        notes: Additional notes (optional)

    Returns:
        AuditLog: Created audit log entry
    """
    return log_audit(
        record_type=record_type,
        record_id=instance.id,
        action=action,
        reason=reason,
        notes=notes,
        user=user
    )


def get_audit_history(record_type, record_id, limit=None):
    """
    Retrieve audit history for a specific record.

    Args:
        record_type: Type of record ('transaction', 'deposit', etc.)
        record_id: ID of the record
        limit: Maximum number of entries to return (optional)

    Returns:
        list: AuditLog entries ordered by created_at desc
    """
    query = AuditLog.query.filter_by(
        record_type=record_type,
        record_id=record_id
    ).order_by(AuditLog.created_at.desc())

    if limit:
        query = query.limit(limit)

    return query.all()


def get_recent_audits(record_type=None, user_id=None, action=None, limit=50):
    """
    Retrieve recent audit logs with optional filters.

    Args:
        record_type: Filter by record type (optional)
        user_id: Filter by user ID (optional)
        action: Filter by action (optional)
        limit: Maximum number of entries to return (default 50)

    Returns:
        list: AuditLog entries ordered by created_at desc
    """
    query = AuditLog.query

    if record_type:
        query = query.filter_by(record_type=record_type)

    if user_id:
        query = query.filter_by(user_id=user_id)

    if action:
        query = query.filter_by(action=action)

    query = query.order_by(AuditLog.created_at.desc())

    if limit:
        query = query.limit(limit)

    return query.all()
