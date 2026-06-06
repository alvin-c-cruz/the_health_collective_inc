"""
Audit Trail Viewer Routes

Provides comprehensive audit log viewing with filtering and pagination.
Accessible only to Admin and Accountant roles.
"""

from datetime import datetime

from flask import render_template, request
from flask_login import current_user, login_required
from sqlalchemy import or_

from application.blueprints.audit import bp
from application.blueprints.audit.models import AuditLog, LoginHistory
from application.blueprints.user.models import User
from application.extensions import db


def is_admin_or_accountant():
    """Check if current user is admin or has accountant role"""
    if not current_user or not current_user.is_authenticated:
        return False
    return current_user.admin or current_user.superuser


@bp.route("/audit-log")
@login_required
def audit_log():
    """
    Main audit log viewer with filtering and pagination.

    Filters:
    - module: Filter by module name
    - action: Filter by action type
    - user_id: Filter by user
    - date_from: Start date
    - date_to: End date
    - search: Search in record_identifier, notes, reason

    Pagination:
    - page: Page number (default 1)
    - per_page: Items per page (default 50)
    """
    # Check permissions
    if not is_admin_or_accountant():
        return render_template(
            "error.html",
            error_title="Access Denied",
            error_message="You do not have permission to view audit logs. Only Admin and Accountant users can access this page.",
        ), 403

    # Get filter parameters
    module_filter = request.args.get("module", "").strip()
    action_filter = request.args.get("action", "").strip()
    user_id_filter = request.args.get("user_id", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()
    search = request.args.get("search", "").strip()

    # Get pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Build query
    query = AuditLog.query

    # Apply filters
    if module_filter:
        query = query.filter(AuditLog.module == module_filter)

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    if user_id_filter:
        query = query.filter(AuditLog.user_id == int(user_id_filter))

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(AuditLog.timestamp >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            # Include the entire day
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.timestamp <= date_to_obj)
        except ValueError:
            pass

    if search:
        # Search in record_identifier, notes, reason
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.record_identifier.ilike(search_pattern),
                AuditLog.notes.ilike(search_pattern),
                AuditLog.reason.ilike(search_pattern),
            )
        )

    # Order by timestamp descending (most recent first)
    query = query.order_by(AuditLog.timestamp.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    audit_logs = pagination.items

    # Get available modules (distinct)
    available_modules = (
        db.session.query(AuditLog.module).distinct().order_by(AuditLog.module).all()
    )
    available_modules = [m[0] for m in available_modules if m[0]]

    # Get available actions (distinct)
    available_actions = (
        db.session.query(AuditLog.action).distinct().order_by(AuditLog.action).all()
    )
    available_actions = [a[0] for a in available_actions if a[0]]

    # Get available users (who have audit logs)
    available_users = (
        db.session.query(User)
        .join(AuditLog, AuditLog.user_id == User.id)
        .distinct()
        .order_by(User.user_name)
        .all()
    )

    # Calculate statistics
    total_logs = query.count()
    if date_from or date_to:
        stats_period = f"{date_from or 'beginning'} to {date_to or 'now'}"
    else:
        stats_period = "all time"

    return render_template(
        "audit/audit_log.html",
        audit_logs=audit_logs,
        pagination=pagination,
        # Filters
        module_filter=module_filter,
        action_filter=action_filter,
        user_id_filter=user_id_filter,
        date_from=date_from,
        date_to=date_to,
        search=search,
        # Available options
        available_modules=available_modules,
        available_actions=available_actions,
        available_users=available_users,
        # Statistics
        total_logs=total_logs,
        stats_period=stats_period,
        # Pagination
        per_page=per_page,
    )


@bp.route("/login-history")
@login_required
def login_history():
    """
    Login history viewer.

    Accessible only to Admin users.
    """
    # Check permissions (more restrictive - admin only)
    if not current_user.is_authenticated or not (
        current_user.admin or current_user.superuser
    ):
        return render_template(
            "error.html",
            error_title="Access Denied",
            error_message="You do not have permission to view login history. Only Admin users can access this page.",
        ), 403

    # Get filter parameters
    user_id_filter = request.args.get("user_id", "").strip()
    status_filter = request.args.get("status", "").strip()
    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # Get pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    # Build query
    query = LoginHistory.query

    # Apply filters
    if user_id_filter:
        query = query.filter(LoginHistory.user_id == int(user_id_filter))

    if status_filter:
        query = query.filter(LoginHistory.status == status_filter)

    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(LoginHistory.login_time >= date_from_obj)
        except ValueError:
            pass

    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
            date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
            query = query.filter(LoginHistory.login_time <= date_to_obj)
        except ValueError:
            pass

    # Order by login_time descending
    query = query.order_by(LoginHistory.login_time.desc())

    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    login_logs = pagination.items

    # Get available users
    available_users = (
        db.session.query(User)
        .join(LoginHistory, LoginHistory.user_id == User.id)
        .distinct()
        .order_by(User.user_name)
        .all()
    )

    # Calculate statistics
    total_logs = query.count()
    total_success = query.filter(LoginHistory.status == "success").count()
    total_failed = query.filter(LoginHistory.status == "failed").count()

    return render_template(
        "audit/login_history.html",
        login_logs=login_logs,
        pagination=pagination,
        # Filters
        user_id_filter=user_id_filter,
        status_filter=status_filter,
        date_from=date_from,
        date_to=date_to,
        # Available options
        available_users=available_users,
        # Statistics
        total_logs=total_logs,
        total_success=total_success,
        total_failed=total_failed,
        # Pagination
        per_page=per_page,
    )
