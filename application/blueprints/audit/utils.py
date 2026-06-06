"""
Audit Logging Utilities

Helper functions for consistent audit trail logging across all modules.
Based on CAS pattern with improvements.

Usage:
    from application.blueprints.audit.utils import log_create, log_update, log_delete

    # Create
    log_create('customer', customer.id, f'{customer.code} - {customer.name}',
               new_values=model_to_dict(customer, ['code', 'name', 'email', 'phone']))

    # Update
    old_values = model_to_dict(customer, [...])
    # ... make changes ...
    new_values = model_to_dict(customer, [...])
    log_update('customer', customer.id, f'{customer.code} - {customer.name}',
               old_values=old_values, new_values=new_values)

    # Delete
    old_values = model_to_dict(customer, [...])
    identifier = f'{customer.code} - {customer.name}'
    record_id = customer.id
    # ... delete customer ...
    log_delete('customer', record_id, identifier, old_values=old_values)
"""

from datetime import datetime

from flask import request
from flask_login import current_user

from application.blueprints.audit.models import AuditLog, LoginHistory
from application.extensions import db


def get_client_ip():
    """
    Get client IP address, handling proxies.

    Returns the real client IP even behind reverse proxies.
    """
    if request.headers.get("X-Forwarded-For"):
        # Behind proxy - get first IP in chain
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    return request.remote_addr


def get_user_agent():
    """Get user agent string, truncated to max length"""
    user_agent = request.headers.get("User-Agent", "")
    return user_agent[:500] if user_agent else None


def get_user_info():
    """
    Get current user information for audit logging.

    Returns tuple: (user_id, username, full_name)
    Returns (None, None, None) if no user is authenticated.
    """
    if current_user and current_user.is_authenticated:
        user_id = current_user.id
        username = current_user.user_name
        full_name = f"{current_user.first_name} {current_user.last_name}"
        return user_id, username, full_name
    return None, None, None


def log_audit(
    module,
    action,
    record_id=None,
    record_identifier=None,
    old_values=None,
    new_values=None,
    reason=None,
    notes=None,
    user=None,
):
    """
    Generic audit logging function.

    Args:
        module: Module name (e.g., 'customer', 'transaction', 'journal')
        action: Action performed (e.g., 'created', 'updated', 'deleted', 'submitted', 'approved')
        record_id: ID of the affected record
        record_identifier: Human-readable identifier (e.g., "CUST-001 - ABC Corp")
        old_values: Dict of old field values (for updates/deletes)
        new_values: Dict of new field values (for creates/updates)
        reason: Reason for change (optional)
        notes: Additional notes (optional)
        user: User object (optional, defaults to current_user)

    Returns:
        AuditLog instance (not committed - caller controls transaction)
    """
    try:
        # Get user info
        if user:
            user_id = user.id
            username = user.user_name
            full_name = f"{user.first_name} {user.last_name}"
        else:
            user_id, username, full_name = get_user_info()

        # Create audit log entry
        audit = AuditLog(
            module=module,
            action=action,
            record_id=record_id,
            record_identifier=record_identifier,
            user_id=user_id,
            username=username,
            full_name=full_name,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
            reason=reason,
            notes=notes,
        )

        # Set values using properties (which handle JSON serialization)
        if old_values:
            audit.old_values = old_values
        if new_values:
            audit.new_values = new_values

        # Add to session but DON'T commit
        # Caller controls transaction to ensure atomicity
        db.session.add(audit)

        return audit

    except Exception as e:
        # Audit failures should not break main operations
        # Log the error but don't raise
        print(f"Audit logging error: {e}")
        return None


def log_create(module, record_id, record_identifier, new_values, notes=None, user=None):
    """
    Log record creation.

    Args:
        module: Module name
        record_id: ID of created record
        record_identifier: Human-readable identifier
        new_values: Dict of field values
        notes: Optional notes
        user: Optional user object

    Returns:
        AuditLog instance
    """
    return log_audit(
        module=module,
        action="created",
        record_id=record_id,
        record_identifier=record_identifier,
        new_values=new_values,
        notes=notes,
        user=user,
    )


def log_update(
    module,
    record_id,
    record_identifier,
    old_values,
    new_values,
    reason=None,
    notes=None,
    user=None,
):
    """
    Log record update.

    Args:
        module: Module name
        record_id: ID of updated record
        record_identifier: Human-readable identifier
        old_values: Dict of old field values
        new_values: Dict of new field values
        reason: Optional reason for update
        notes: Optional notes
        user: Optional user object

    Returns:
        AuditLog instance
    """
    return log_audit(
        module=module,
        action="updated",
        record_id=record_id,
        record_identifier=record_identifier,
        old_values=old_values,
        new_values=new_values,
        reason=reason,
        notes=notes,
        user=user,
    )


def log_delete(
    module, record_id, record_identifier, old_values, reason=None, notes=None, user=None
):
    """
    Log record deletion.

    Args:
        module: Module name
        record_id: ID of deleted record
        record_identifier: Human-readable identifier
        old_values: Dict of field values before deletion
        reason: Optional reason for deletion
        notes: Optional notes
        user: Optional user object

    Returns:
        AuditLog instance
    """
    return log_audit(
        module=module,
        action="deleted",
        record_id=record_id,
        record_identifier=record_identifier,
        old_values=old_values,
        reason=reason,
        notes=notes,
        user=user,
    )


def log_status_change(
    module,
    record_id,
    record_identifier,
    action,
    old_status=None,
    new_status=None,
    reason=None,
    notes=None,
    user=None,
    context_values=None,
):
    """
    Log status/workflow changes (submitted, approved, cancelled, etc.)

    Args:
        module: Module name
        record_id: ID of record
        record_identifier: Human-readable identifier
        action: Action performed (e.g., 'submitted', 'approved', 'cancelled')
        old_status: Previous status (optional)
        new_status: New status (optional)
        reason: Optional reason for change
        notes: Optional notes
        user: Optional user object
        context_values: Optional dict of contextual fields to include (e.g., {'bank_name': 'BDO', 'account_number': '123'})

    Returns:
        AuditLog instance
    """
    old_values = {"status": old_status} if old_status else {}
    new_values = {"status": new_status} if new_status else {}

    # Add contextual fields to both old and new values (these show what record was affected)
    if context_values:
        old_values.update(context_values)
        new_values.update(context_values)

    return log_audit(
        module=module,
        action=action,
        record_id=record_id,
        record_identifier=record_identifier,
        old_values=old_values if old_values else None,
        new_values=new_values if new_values else None,
        reason=reason,
        notes=notes,
        user=user,
    )


def model_to_dict(instance, fields):
    """
    Convert SQLAlchemy model instance to dictionary for specified fields.

    Args:
        instance: SQLAlchemy model instance
        fields: List of field names to include

    Returns:
        Dict with field values

    Example:
        values = model_to_dict(customer, ['code', 'name', 'email', 'phone', 'is_active'])
    """
    result = {}
    for field in fields:
        if hasattr(instance, field):
            value = getattr(instance, field)

            # Convert datetime to string for JSON serialization
            if isinstance(value, datetime):
                value = value.isoformat()

            result[field] = value

    return result


def get_changes(old_obj, new_data, fields):
    """
    Compare old object with new data and return only changed fields.

    Args:
        old_obj: Original SQLAlchemy model instance
        new_data: Dict of new field values
        fields: List of fields to compare

    Returns:
        Tuple of (old_values, new_values) dicts containing only changed fields

    Example:
        old_vals, new_vals = get_changes(customer, form.data, ['name', 'email', 'phone'])
    """
    old_values = {}
    new_values = {}

    for field in fields:
        if field not in new_data:
            continue

        old_val = getattr(old_obj, field, None)
        new_val = new_data[field]

        # Convert datetime for comparison
        if isinstance(old_val, datetime):
            old_val = old_val.isoformat()

        # Only include if changed
        if old_val != new_val:
            old_values[field] = old_val
            new_values[field] = new_val

    return old_values, new_values


def get_record_identifier(instance):
    """
    Get human-readable identifier for any model instance.

    Uses common patterns to generate meaningful identifiers.

    Args:
        instance: SQLAlchemy model instance

    Returns:
        String identifier

    Example:
        identifier = get_record_identifier(customer)  # "CUST-001 - ABC Corp"
    """
    # Pattern 1: code + name
    if hasattr(instance, "code") and hasattr(instance, "name"):
        return f"{instance.code} - {instance.name}"

    # Pattern 2: record_number
    if hasattr(instance, "record_number"):
        return instance.record_number

    # Pattern 3: just name
    if hasattr(instance, "name"):
        return instance.name

    # Pattern 4: username (for users)
    if hasattr(instance, "user_name"):
        full_name = ""
        if hasattr(instance, "first_name") and hasattr(instance, "last_name"):
            full_name = f" - {instance.first_name} {instance.last_name}"
        return f"{instance.user_name}{full_name}"

    # Fallback: class name + ID
    class_name = instance.__class__.__name__
    return f"{class_name} #{instance.id}"


def log_login(user, status="success", failure_reason=None):
    """
    Log login attempt (success or failure).

    Args:
        user: User object (or username string if failed)
        status: 'success' or 'failed'
        failure_reason: Reason for failure (if status='failed')

    Returns:
        LoginHistory instance
    """
    try:
        # Handle user object or username string
        if isinstance(user, str):
            user_id = None
            username = user
            full_name = None
        else:
            user_id = user.id
            username = user.user_name
            full_name = f"{user.first_name} {user.last_name}"

        login = LoginHistory(
            user_id=user_id,
            username=username,
            full_name=full_name,
            status=status,
            failure_reason=failure_reason,
            ip_address=get_client_ip(),
            user_agent=get_user_agent(),
        )

        db.session.add(login)
        db.session.commit()

        return login

    except Exception as e:
        print(f"Login history logging error: {e}")
        return None
