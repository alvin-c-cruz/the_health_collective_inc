"""
Role-based permission helpers for The Health Collective Inc.

User Role Hierarchy:
- SuperUser: Can delegate admin & other types, can delegate another SuperUser
- Admin: SuperUser who cannot be demoted, approves record submissions/changes
- Staff: Can enter transactions (draft/submitted), request modifications, view reports
- View: Read-only access to reports, no CRUD operations
"""
from functools import wraps
from flask import flash, redirect, url_for, session
from application.blueprints.user.models import User


def get_current_user():
    """Get the current logged-in user from session"""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None


def is_superuser(user=None):
    """Check if user is a SuperUser"""
    if user is None:
        user = get_current_user()
    return user and user.is_superuser


def is_admin(user=None):
    """Check if user is Admin or SuperUser"""
    if user is None:
        user = get_current_user()
    return user and (user.is_admin or user.is_superuser)


def is_staff(user=None):
    """Check if user is Staff (or higher)"""
    if user is None:
        user = get_current_user()
    return user and (user.is_staff or user.is_admin or user.is_superuser)


def is_view(user=None):
    """Check if user has at least view permissions"""
    if user is None:
        user = get_current_user()
    return user and (user.is_view or user.is_staff or user.is_admin or user.is_superuser)


def can_manage_users(user=None):
    """Admin or SuperUser can manage users"""
    return is_admin(user)


def can_delegate_superuser(user=None):
    """Only SuperUser can delegate SuperUser rights"""
    return is_superuser(user)


def can_approve_submissions(user=None):
    """Admin or SuperUser can approve submitted transactions → posted"""
    return is_admin(user)


def can_approve_change_requests(user=None):
    """Admin or SuperUser can approve change requests"""
    return is_admin(user)


def can_direct_edit(user=None):
    """Only SuperUser can bypass approval cycle with direct edits"""
    return is_superuser(user)


def can_create_transactions(user=None):
    """Staff or higher can create transactions"""
    return is_staff(user)


def can_submit_transactions(user=None):
    """Staff or higher can submit draft transactions"""
    return is_staff(user)


def can_request_changes(user=None):
    """Staff or higher can request changes to posted transactions"""
    return is_staff(user)


def can_view_reports(user=None):
    """Anyone with view access or higher can view reports"""
    return is_view(user)


# Decorators for views

def superuser_required(f):
    """Decorator: Require SuperUser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not is_superuser(user):
            flash('SuperUser access required.', 'danger')
            return redirect(url_for('daily_sales.index'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator: Require Admin or SuperUser access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not is_admin(user):
            flash('Admin access required.', 'danger')
            return redirect(url_for('daily_sales.index'))
        return f(*args, **kwargs)
    return decorated_function


def staff_required(f):
    """Decorator: Require Staff or higher access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not is_staff(user):
            flash('Staff access required.', 'danger')
            return redirect(url_for('daily_sales.index'))
        return f(*args, **kwargs)
    return decorated_function


def view_required(f):
    """Decorator: Require View or higher access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not is_view(user):
            flash('Access denied.', 'danger')
            return redirect(url_for('daily_sales.index'))
        return f(*args, **kwargs)
    return decorated_function
