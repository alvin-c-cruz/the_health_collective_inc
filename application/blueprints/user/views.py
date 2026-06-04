from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, current_user, logout_user
from functools import wraps
from collections import defaultdict
from werkzeug.security import generate_password_hash

from .models import User, Role, UserRole
from .forms import LoginForm, UserForm

from application.extensions import db
from application.blueprints.audit.utils import (
    log_create, log_update, log_delete, log_status_change, log_login,
    model_to_dict, get_record_identifier
)

# Maps role name -> (parent_group, sub_group). '' sub_group = no sub-header.
_ROLE_CATEGORIES = {
    'Daily Sales':            ('Operations', ''),
    'Service Types':          ('Operations', ''),
    'Bank Account':           ('Operations', ''),
    'Collections':            ('Operations', ''),

    'Accounts Payable':       ('Accounting', 'Books of Accounts'),
    'Disbursement':           ('Accounting', 'Books of Accounts'),
    'General':                ('Accounting', 'Books of Accounts'),
    'Receipt':                ('Accounting', 'Books of Accounts'),
    'Sales':                  ('Accounting', 'Books of Accounts'),
    'Accounts Payable Extra': ('Accounting', 'Books of Accounts Extra'),
    'Disbursement Extra':     ('Accounting', 'Books of Accounts Extra'),
    'General Extra':          ('Accounting', 'Books of Accounts Extra'),
    'Receipt Extra':          ('Accounting', 'Books of Accounts Extra'),
    'Sales Extra':            ('Accounting', 'Books of Accounts Extra'),
    'Account':                ('Accounting', 'Accounts'),
    'Account Class':          ('Accounting', 'Accounts'),
    'Account Type':           ('Accounting', 'Accounts'),
    'Trial Balance':          ('Accounting', 'Reports'),
    'Ledger':                 ('Accounting', 'Reports'),

    'Customer':               ('Register', ''),
    'Measure':                ('Register', ''),
    'Product':                ('Register', ''),
    'Product Type':           ('Register', ''),
    'Sex':                    ('Register', ''),
    'Tender':                 ('Register', ''),
    'Vendor':                 ('Register', ''),

    'user':                   ('System', ''),
}

_PARENT_ORDER = ['Operations', 'Accounting', 'Register', 'System', 'Other']
_SUB_ORDER    = ['Books of Accounts', 'Books of Accounts Extra', 'Accounts', 'Reports', '']


def _group_roles(roles):
    """Return nested structure: [(parent, [(subgroup, [roles])])]."""
    # bucket: parent -> subgroup -> [roles]
    buckets = defaultdict(lambda: defaultdict(list))
    for role in roles:
        parent, sub = _ROLE_CATEGORIES.get(role.role_name, ('Other', ''))
        buckets[parent][sub].append(role)

    result = []
    for parent in _PARENT_ORDER:
        if parent not in buckets:
            continue
        subs = buckets[parent]
        sub_list = []
        for sub in _SUB_ORDER:
            if sub in subs:
                sub_list.append((sub, sorted(subs[sub], key=lambda r: r.role_name)))
        # Any subs not in _SUB_ORDER (shouldn't happen, but safe fallback)
        for sub, sub_roles in subs.items():
            if sub not in _SUB_ORDER:
                sub_list.append((sub, sorted(sub_roles, key=lambda r: r.role_name)))
        result.append((parent, sub_list))
    return result


bp = Blueprint("user", __name__, template_folder="pages", url_prefix="/user")


def login_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('user.login'))
        
        if not current_user.is_active():
            return redirect(url_for("user.inactive"))
                
        return func(*args, **kwargs)
    return decorated_view


def roles_accepted(roles=[]):
    def decorator(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not any(role in roles for role in current_user.user_roles):
                flash("You are not allowed to access this area.", category="error")
                return redirect(url_for('dashboard.home')) 
            return func(*args, **kwargs)
        return decorated_view
    return decorator  


@bp.route("/")
@login_required
def home():
    return "User profile"


@bp.route("/list")
@login_required
@roles_accepted(['user'])
def user_list():
    users = User.query.order_by('user_name').all()
    context = {
        "rows": users,
    }
    return render_template("user/user_list.html", **context)


@bp.route("/user_group/<int:record_id>")
@login_required
@roles_accepted(['user'])
def user_group(record_id):
    user = User.query.get(record_id)
    roles = Role.query.order_by('role_name').all()
    context = {
        "user": user,
        "roles": roles,
        "role_groups": _group_roles(roles),
        "assigned_count": sum(1 for r in roles if r.role_name in user.user_roles),
        "total_count": len(roles),
    }
    return render_template("user/user_group.html", **context)


@bp.route("user_admin")
@login_required
@roles_accepted(['user'])
def user_admin():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))

    user = User.query.get(user_id)
    if user.user_name != "admin":
        old_value = user.admin
        user.admin = value

        # Log admin status change
        log_status_change(
            module='user',
            record_id=user.id,
            record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
            action='admin_changed',
            old_status='enabled' if old_value else 'disabled',
            new_status='enabled' if value else 'disabled',
            notes=f'Admin status {"enabled" if value else "disabled"}'
        )

        db.session.commit()
    else:
        flash("Cannot change the master admin account.", category="error")
    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("user_superuser")
@login_required
@roles_accepted(['user'])
def user_superuser():
    if not current_user.superuser:
        flash("Only a SuperAdmin can grant or revoke SuperAdmin status.", category="error")
        return redirect(url_for('user.user_list'))
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))
    user = User.query.get(user_id)
    if user.user_name != "admin":
        old_value = user.superuser
        user.superuser = value

        # Log superuser status change
        log_status_change(
            module='user',
            record_id=user.id,
            record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
            action='superuser_changed',
            old_status='enabled' if old_value else 'disabled',
            new_status='enabled' if value else 'disabled',
            notes=f'Superuser status {"enabled" if value else "disabled"}'
        )

        db.session.commit()
    else:
        flash("Cannot change the master admin account.", category="error")
    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("user_staff")
@login_required
@roles_accepted(['user'])
def user_staff():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))
    user = User.query.get(user_id)
    if user.user_name != "admin":
        old_value = user.staff
        user.staff = value

        # Log staff status change
        log_status_change(
            module='user',
            record_id=user.id,
            record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
            action='staff_changed',
            old_status='enabled' if old_value else 'disabled',
            new_status='enabled' if value else 'disabled',
            notes=f'Staff status {"enabled" if value else "disabled"}'
        )

        db.session.commit()
    else:
        flash("Cannot change the master admin account.", category="error")
    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("user/active")
@login_required
@roles_accepted(['user'])
def user_active():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))

    user = User.query.get(user_id)
    if user.user_name != "admin":
        old_value = user.active
        user.active = value

        # Log active status change
        log_status_change(
            module='user',
            record_id=user.id,
            record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
            action='active_changed',
            old_status='active' if old_value else 'inactive',
            new_status='active' if value else 'inactive',
            notes=f'User {"activated" if value else "deactivated"}'
        )

        db.session.commit()
    else:
        flash("Cannot change super admin status", category="error")

    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("toggle_superuser")
@login_required
@roles_accepted(['user'])
def toggle_superuser():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))

    user = User.query.get(user_id)
    if user.user_name != "admin":
        user.is_superuser = value
        db.session.commit()
        flash(f"SuperUser status {'enabled' if value else 'disabled'} for {user.user_name}", category="success")
    else:
        flash("Cannot change super admin status", category="error")

    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("toggle_admin")
@login_required
@roles_accepted(['user'])
def toggle_admin():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))

    user = User.query.get(user_id)
    if user.user_name != "admin":
        user.is_admin = value
        db.session.commit()
        flash(f"Administrator status {'enabled' if value else 'disabled'} for {user.user_name}", category="success")
    else:
        flash("Cannot change super admin status", category="error")

    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("toggle_staff")
@login_required
@roles_accepted(['user'])
def toggle_staff():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))

    user = User.query.get(user_id)
    user.is_staff = value
    db.session.commit()
    flash(f"Staff status {'enabled' if value else 'disabled'} for {user.user_name}", category="success")

    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("toggle_viewer")
@login_required
@roles_accepted(['user'])
def toggle_viewer():
    user_id = request.args.get('user_id')
    value = int(request.args.get("value"))

    user = User.query.get(user_id)
    user.is_view = value
    db.session.commit()
    flash(f"Viewer status {'enabled' if value else 'disabled'} for {user.user_name}", category="success")

    return redirect(url_for('user.user_group', record_id=user_id))


@bp.route("/toggle_maintenance_mode", methods=["POST"])
@login_required
def toggle_maintenance_mode():
    """Toggle maintenance mode - only accessible to superusers"""
    if not current_user.is_superuser:
        flash("Only superusers can toggle maintenance mode.", category="error")
        return redirect(url_for('dashboard.home'))

    from flask import current_app
    from pathlib import Path

    # Path to config file - use Flask's instance_path
    config_path = Path(current_app.instance_path) / 'config.py'

    # Read current config
    with open(config_path, 'r') as f:
        config_content = f.read()

    # Toggle MAINTENANCE_MODE
    if 'MAINTENANCE_MODE = True' in config_content:
        new_content = config_content.replace('MAINTENANCE_MODE = True', 'MAINTENANCE_MODE = False')
        new_status = False
        message = "Maintenance mode DISABLED. Site is now accessible to all users."
    else:
        new_content = config_content.replace('MAINTENANCE_MODE = False', 'MAINTENANCE_MODE = True')
        new_status = True
        message = "Maintenance mode ENABLED. Only superusers can access the site."

    # Write updated config
    with open(config_path, 'w') as f:
        f.write(new_content)

    # Update runtime config
    current_app.config['MAINTENANCE_MODE'] = new_status

    flash(message, category="success")
    return redirect(request.referrer or url_for('dashboard.home'))


@bp.route("/login", methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect("/")

    if request.method == "POST":
        form = LoginForm()
        form.post(request.form)

        if form.validate():
            user = User.query.filter_by(user_name=form.user_name).first()
            if user:
                if user.check_pass_word(form.pass_word):
                    # Check if maintenance mode is active and user is not a superuser
                    if current_app.config.get('MAINTENANCE_MODE', False):
                        if not user.superuser:
                            # Log failed login due to maintenance mode
                            log_login(user, status='failed', failure_reason='Site in maintenance mode')
                            return redirect(url_for('maintenance'))

                    # Log successful login
                    log_login(user, status='success')

                    login_user(user)
                    flash(f"Welcome {user.user_name}.", category="success")
                    return redirect("/")
                else:
                    # Log failed login - wrong password
                    log_login(form.user_name, status='failed', failure_reason='Invalid password')
            else:
                # Log failed login - user not found
                log_login(form.user_name, status='failed', failure_reason='User not found')

            flash("Invalid username / password.", category="error")
    else:
        form = LoginForm()

    check_roles()

    context = {
        "form": form,
    }
    return render_template("user/login.html", **context)


@bp.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        form = UserForm()
        form.post(request.form)
        if form.validate():
            user = User(
                user_name=form.user_name,
                first_name=form.first_name,
                middle_name=form.middle_name,
                last_name=form.last_name,
                email=form.email
            )
            
            if form.user_name == "admin":
                user.active = True
                user.superuser = True
                user.admin = True
                
            user.set_pass_word(form.pass_word)

            db.session.add(user)
            db.session.flush()  # Get ID without committing

            # Log user creation
            log_create(
                module='user',
                record_id=user.id,
                record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
                new_values=model_to_dict(user, [
                    'user_name', 'first_name', 'middle_name', 'last_name', 'email',
                    'admin', 'staff', 'superuser', 'active'
                ]),
                notes='User self-registration'
            )

            db.session.commit()

            if form.user_name == "admin":
                if not Role.query.all():
                    check_roles()
                
                role = Role.query.filter_by(role_name="user").first()
                                    
                user_role = UserRole(
                    user_id=user.id,
                    role_id=role.id
                )
                
                db.session.add(user_role)
                db.session.commit()               
            
            login_user(user)
            flash(f"Welcome {user.user_name}.", category="success")
            return redirect(url_for("user.inactive"))
        
    else:
        form = UserForm()
    
    context = {
        "form": form
    }
    return render_template("user/register.html", **context)


@bp.route("/change_password", methods=["POST", "GET"])
@login_required
def change_password():
    if not current_user.admin:
        flash("Admin rights required", category="error")
        return redirect(url_for('dashboard.home'))
    

    if request.method == "POST":
        form = UserForm()
        form.post(request.form)

        user = User.query.filter_by(user_name=form.user_name).first()

        if not user:
            flash("User does not exists.", category="error")
        elif form.pass_word != form.confirm_pass_word:
            flash("Password is not identical.", category="error")
        else:              
            form.id = user.id
            user.set_pass_word(form.pass_word)
            db.session.commit()
            
            flash(f"Password has changed.", category="success")
            return redirect(url_for("main.home"))
        
    else:
        form = UserForm()
    
    context = {
        "form": form
    }
    return render_template("user/change_password.html", **context)


@bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("User logged out.", category="success")
        
    return redirect(url_for('user.login'))


@bp.route("/inactive")
def inactive():
    if current_user.is_active():
        return redirect("/")
    
    return render_template("user/inactive.html")


@bp.route("/add_role")
@login_required
@roles_accepted(['user'])
def add_role():
    user_id = int(request.args.get("user_id"))
    role_id = int(request.args.get("role_id"))

    user = User.query.get(user_id)
    role = Role.query.get(role_id)

    user_role = UserRole(
        user_id=user_id,
        role_id=role_id
    )

    db.session.add(user_role)

    # Log role assignment
    log_status_change(
        module='user',
        record_id=user.id,
        record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
        action='role_added',
        new_status=role.role_name,
        notes=f'Role "{role.role_name}" granted'
    )

    db.session.commit()

    return redirect(url_for('user.user_group', record_id=user_id))
    
@bp.route("/remove_role")
@login_required
@roles_accepted(['user'])
def remove_role():
    user_id = int(request.args.get("user_id"))
    role_id = int(request.args.get("role_id"))

    user = User.query.get(user_id)
    role = Role.query.get(role_id)

    if user.user_name == 'admin' and role.role_name == 'user':
        flash("Cannot remove user role for super admin", category='error')
    else:
        user_role = UserRole.query.filter_by(
            user_id=user_id,
            role_id=role_id
        ).first()

        db.session.delete(user_role)

        # Log role removal
        log_status_change(
            module='user',
            record_id=user.id,
            record_identifier=f"{user.user_name} - {user.first_name} {user.last_name}",
            action='role_removed',
            old_status=role.role_name,
            notes=f'Role "{role.role_name}" revoked'
        )

        db.session.commit()

    return redirect(url_for('user.user_group', record_id=user_id))


def check_roles():
    from application import blueprints
    modules = [
        getattr(blueprints, module)
        for module in dir(blueprints) if hasattr(getattr(blueprints, module), "bp")
    ]
    expected = {'user'}
    for module in modules:
        if hasattr(module, "menu_label"):
            expected.add(getattr(module, "menu_label")[2])

    # Add missing roles
    for role_name in expected:
        if not Role.query.filter_by(role_name=role_name).first():
            db.session.add(Role(role_name=role_name))

    # Remove roles that no longer correspond to any module
    for role in Role.query.all():
        if role.role_name not in expected:
            UserRole.query.filter_by(role_id=role.id).delete()
            db.session.delete(role)

    db.session.commit()

    # Assign all roles to the super admin
    admin = User.query.filter_by(user_name='admin').first()
    if admin:
        assigned_role_ids = {ur.role_id for ur in admin.roles}
        for role in Role.query.all():
            if role.id not in assigned_role_ids:
                db.session.add(UserRole(user_id=admin.id, role_id=role.id))
        db.session.commit()


# ============================================================================
# NEW USER ROLE MANAGEMENT (is_superuser, is_admin, is_staff, is_view)
# ============================================================================

ROLES = ["is_superuser", "is_admin", "is_staff", "is_view"]


@bp.route("/user_management")
@login_required
def user_management():
    """List all users and allow role management"""
    from flask import session
    user_id = session.get('user_id')
    current_user_obj = User.query.get(user_id) if user_id else None

    # Only superuser or admin can access
    if not current_user_obj or not (current_user_obj.is_superuser or current_user_obj.is_admin):
        flash("Access denied. Admin or SuperUser required.", "danger")
        return redirect(url_for('dashboard.home'))

    users = User.query.order_by(User.user_name).all()
    return render_template("user/user_management.html", users=users, roles=ROLES, current_user_obj=current_user_obj)


@bp.route("/update_user_roles/<int:user_id>", methods=["POST"])
@login_required
def update_user_roles(user_id):
    """Update user roles"""
    from flask import session
    current_user_id = session.get('user_id')
    current_user_obj = User.query.get(current_user_id) if current_user_id else None

    # Only superuser or admin can access
    if not current_user_obj or not (current_user_obj.is_superuser or current_user_obj.is_admin):
        flash("Access denied.", "danger")
        return redirect(url_for('user.user_management'))

    user = User.query.get_or_404(user_id)

    # Prevent modifying own account
    if user.id == current_user_obj.id:
        flash("You cannot modify your own account here.", "warning")
        return redirect(url_for('user.user_management'))

    # Prevent demoting protected admins (users with is_admin=True)
    if user.is_admin and not request.form.get("is_admin"):
        flash(f"User '{user.user_name}' is a protected admin and cannot be demoted.", "danger")
        return redirect(url_for('user.user_management'))

    # Only superuser can grant/revoke superuser rights
    if "is_superuser" in request.form:
        if not current_user_obj.is_superuser:
            flash("Only a SuperUser can grant SuperUser rights.", "danger")
            return redirect(url_for('user.user_management'))
        user.is_superuser = bool(request.form.get("is_superuser"))

    # Update other roles
    user.is_admin = bool(request.form.get("is_admin"))
    user.is_staff = bool(request.form.get("is_staff"))
    user.is_view = bool(request.form.get("is_view"))
    user.active = bool(request.form.get("active"))

    db.session.commit()
    flash(f"User '{user.user_name}' roles updated successfully.", "success")
    return redirect(url_for('user.user_management'))
