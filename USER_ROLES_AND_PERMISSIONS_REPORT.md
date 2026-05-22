# User Roles and Permissions Report
## The Health Collective Inc. - Complete Analysis

**Date:** 2026-05-22
**Analyzed By:** Claude (AI Assistant)
**Project:** The Health Collective Inc. - User Management System

---

## Executive Summary

The Health Collective Inc. uses a **dual-layer permission system** combining:
1. **User Type Flags** (Boolean fields: superuser, admin, staff, active)
2. **Module-Based Roles** (Many-to-many UserRole system for menu access)

This hybrid approach provides both hierarchical permissions (who can approve/edit) and granular module access control (which features are visible).

**Key Findings:**
- 4 user type levels: SuperUser, Admin, Staff, View (implicit)
- 30+ module-based roles for feature access
- Protected "admin" account that cannot be modified
- Hierarchical permission inheritance (SuperUser > Admin > Staff > View)

---

## Table of Contents

1. [User Type System (Boolean Flags)](#1-user-type-system-boolean-flags)
2. [Module-Based Role System](#2-module-based-role-system)
3. [Permission Matrix](#3-permission-matrix)
4. [Database Schema](#4-database-schema)
5. [User Management Interface](#5-user-management-interface)
6. [Special Accounts](#6-special-accounts)
7. [Permission Enforcement Patterns](#7-permission-enforcement-patterns)
8. [Security Analysis](#8-security-analysis)
9. [Usage Examples](#9-usage-examples)
10. [Recommendations](#10-recommendations)

---

## 1. User Type System (Boolean Flags)

### Overview

The User model contains 4 boolean flags that define hierarchical permission levels:

```python
class User(db.Model):
    superuser = db.Column(db.Boolean(), default=False)  # Highest level
    admin = db.Column(db.Boolean(), default=False)      # Approval authority
    staff = db.Column(db.Boolean(), default=False)      # Transaction entry
    active = db.Column(db.Boolean(), default=False)     # Account enabled
```

**Note:** There is no explicit `view` flag in the database, but the permissions system treats users without staff/admin/superuser flags as "View-only" users.

### 1.1 SuperUser

**Database Field:** `User.superuser = True`

**Description:**
- Highest permission level in the system
- Can delegate admin rights and create other SuperUsers
- Can bypass approval workflows with direct edits
- Cannot be demoted by admins (only by other SuperUsers)

**Key Capabilities:**
- ✅ All Admin capabilities (inherits)
- ✅ Delegate SuperUser status to other users
- ✅ Unlock approved transactions (reverse approvals)
- ✅ Direct edit posted records without change requests
- ✅ Modify protected admin accounts (except master "admin")
- ✅ Bypass two-tier approval workflows

**Restrictions:**
- ❌ Cannot modify the master "admin" account
- ❌ Must be granted by existing SuperUser

**Usage Pattern:**
```python
# Permission check
if not current_user.superuser:
    abort(403)

# Decorator (from permissions.py)
@superuser_required
def unlock_transaction(transaction_id):
    ...
```

**Real-World Example:**
- Company owner, CEO
- IT Administrator
- System implementer/consultant

---

### 1.2 Admin

**Database Field:** `User.admin = True`

**Description:**
- Approval authority for submitted transactions
- Can manage users (except SuperUser privileges)
- Can approve change requests and cancellation requests
- Protected status: cannot be demoted once granted (safety mechanism)

**Key Capabilities:**
- ✅ All Staff capabilities (inherits)
- ✅ Approve submitted transactions → posted
- ✅ Disapprove/return transactions to draft
- ✅ Approve change requests
- ✅ Approve fund cancellation requests
- ✅ Approve deposit submissions
- ✅ Post petty cash vouchers
- ✅ Manage user accounts (create, edit, assign roles)
- ✅ Change user passwords
- ✅ Auto-approve own submissions (deposits)
- ✅ View pending approval queues

**Restrictions:**
- ❌ Cannot unlock approved transactions (SuperUser only)
- ❌ Cannot grant/revoke SuperUser status (SuperUser only)
- ❌ Cannot direct edit posted records (SuperUser only)
- ❌ Cannot be demoted (safety protection)

**Usage Pattern:**
```python
# Permission check
if not (current_user.admin or current_user.superuser):
    abort(403)

# Decorator (from permissions.py)
@admin_required
def approve_transaction(transaction_id):
    ...
```

**Real-World Example:**
- Finance Manager
- Accounting Head
- Operations Manager
- Department Supervisor

---

### 1.3 Staff

**Database Field:** `User.staff = True`

**Description:**
- Operational users who create and submit transactions
- Can enter data but require admin approval
- Can request changes to posted records
- Cannot approve or post records

**Key Capabilities:**
- ✅ Create draft transactions
- ✅ Edit own draft transactions
- ✅ Submit transactions for approval
- ✅ Bulk submit multiple transactions
- ✅ Cancel own draft transactions
- ✅ Request changes to posted records (via ChangeRequest)
- ✅ Request cancellation of posted records (two-tier)
- ✅ View reports (module access dependent)
- ✅ Create deposits (requires admin approval)
- ✅ Create fund accountability records
- ✅ Create petty cash vouchers
- ✅ View transaction history

**Restrictions:**
- ❌ Cannot approve submissions
- ❌ Cannot post records
- ❌ Cannot directly edit posted records
- ❌ Cannot manage users
- ❌ Cannot view pending approval queues (admin only)
- ❌ Cannot cancel posted funds (must request approval)

**Usage Pattern:**
```python
# Permission check
if not (current_user.staff or current_user.admin or current_user.superuser):
    abort(403)

# Decorator (from permissions.py)
@staff_required
def create_transaction():
    ...
```

**Real-World Example:**
- Front desk staff
- Cashier
- Sales clerk
- Data entry operator
- Bookkeeper

---

### 1.4 View (Implicit)

**Database Field:** No explicit field (users with `active=True` but no staff/admin/superuser flags)

**Description:**
- Read-only access to reports and dashboards
- Cannot create, edit, or submit any records
- Lowest permission level
- Used for auditors, executives, or external stakeholders

**Key Capabilities:**
- ✅ View reports (if granted module access)
- ✅ View dashboards
- ✅ Export data (read-only)
- ✅ Search/filter records

**Restrictions:**
- ❌ Cannot create transactions
- ❌ Cannot edit anything
- ❌ Cannot submit or approve
- ❌ Cannot request changes
- ❌ No CRUD operations

**Usage Pattern:**
```python
# Permission check
@view_required
def view_report():
    ...
```

**Real-World Example:**
- Auditor
- Executive viewing dashboards
- External accountant
- Compliance officer

---

### 1.5 Active Status

**Database Field:** `User.active = True`

**Description:**
- Controls whether user can log in
- Independent of permission levels
- New users default to inactive (must be activated by admin)

**States:**
- `active=True`: User can log in and access granted features
- `active=False`: User blocked from system (sees "inactive" page)

**Usage Pattern:**
```python
def is_active(self):
    return self.active

# In login_required decorator
if not current_user.is_active():
    return redirect(url_for("user.inactive"))
```

**Account Lifecycle:**
1. User registers → `active=False` (default)
2. Admin activates → `active=True`
3. If terminated → `active=False` (soft delete)

---

## 2. Module-Based Role System

### Overview

In addition to user type flags, the system uses a **many-to-many role assignment** for module access control. This determines which menu items and features are visible.

```python
class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_name = db.Column(db.String())

class UserRole(db.Model):
    user_id = db.Column(db.Integer, ForeignKey('user.id'), primary_key=True)
    role_id = db.Column(db.Integer, ForeignKey('role.id'), primary_key=True)
```

### 2.1 Role Categories

Roles are organized into 4 main categories:

#### **Operations** (5 roles)
| Role Name | Module | Description |
|-----------|--------|-------------|
| Daily Sales | `/daily_sales` | Daily transaction management, deposits, funds |
| Service Types | `/transaction_type` | Configure transaction types |
| Bank Account | `/bank_account` | Bank account management |
| Collections | `/collections` | Collection tracking and reporting |
| APE Batch | `/ape_batch` | Annual Physical Examination batch processing |

#### **Accounting - Books of Accounts** (5 roles)
| Role Name | Module | Description |
|-----------|--------|-------------|
| Accounts Payable | `/books_of_accounts/accounts_payable` | AP transactions |
| Disbursement | `/books_of_accounts/disbursement` | Disbursement journal |
| General | `/books_of_accounts/general` | General journal |
| Receipt | `/books_of_accounts/receipt` | Receipt journal |
| Sales | `/books_of_accounts/sales` | Sales journal |

#### **Accounting - Books of Accounts Extra** (5 roles)
| Role Name | Module | Description |
|-----------|--------|-------------|
| Accounts Payable Extra | `/books_of_accounts_extra/accounts_payable_extra` | Extended AP features |
| Disbursement Extra | `/books_of_accounts_extra/disbursement_extra` | Extended disbursement |
| General Extra | `/books_of_accounts_extra/general_extra` | Extended general journal |
| Receipt Extra | `/books_of_accounts_extra/receipt_extra` | Extended receipts |
| Sales Extra | `/books_of_accounts_extra/sales_extra` | Extended sales |

#### **Accounting - Accounts & Reports** (3 roles)
| Role Name | Module | Description |
|-----------|--------|-------------|
| Account | `/account` | Chart of accounts |
| Account Class | `/account_class` | Account classifications |
| Account Type | `/account_type` | Account types |
| Trial Balance | `/trial_balance` | Trial balance reports |
| Ledger | `/ledger` | General ledger |

#### **Register** (7 roles)
| Role Name | Module | Description |
|-----------|--------|-------------|
| Customer | `/customer` | Customer master file |
| Measure | `/measure` | Unit of measure |
| Product | `/product` | Product/service catalog |
| Product Type | `/product_type` | Product categories |
| Sex | `/sex` | Gender codes |
| Tender | `/tender` | Payment types (cash, card, etc.) |
| Vendor | `/vendor` | Vendor master file |
| Company | `/company` | Company settings |

#### **System** (1 role)
| Role Name | Module | Description |
|-----------|--------|-------------|
| user | `/user` | User management (special role) |

**Total Roles:** 30+ modules

---

### 2.2 Role Assignment Logic

**Automatic Role Assignment:**
- The `check_roles()` function scans all blueprints at startup
- Automatically creates Role records for each module
- Assigns all roles to the master "admin" account

**Manual Assignment:**
- Admins assign roles via `/user/user_group/<user_id>` interface
- Roles displayed in hierarchical groups (Operations, Accounting, Register, System)
- Checkboxes to add/remove module access

**Access Control:**
```python
@bp.route("/some_module")
@login_required
@roles_accepted(['Daily Sales'])  # User must have this role
def some_view():
    ...
```

---

### 2.3 Role vs User Type Interaction

**Important:** Roles and User Types work together:

| Scenario | Result |
|----------|--------|
| User has "Daily Sales" role + Staff flag | Can create/edit transactions |
| User has "Daily Sales" role + Admin flag | Can create/edit AND approve transactions |
| User has "Daily Sales" role + NO flags (View) | Can view but not edit |
| User has Admin flag but NO "Daily Sales" role | Cannot even see the menu (blocked) |

**Takeaway:** Both systems must grant access:
1. **Role** → Determines if menu/module is visible
2. **User Type** → Determines what actions are allowed within module

---

## 3. Permission Matrix

### Complete Capability Matrix

| Capability | View | Staff | Admin | SuperUser |
|------------|------|-------|-------|-----------|
| **Authentication** |
| Login | ✅ | ✅ | ✅ | ✅ |
| Active account required | ✅ | ✅ | ✅ | ✅ |
| **Transactions - Daily Sales** |
| View transactions | ✅ | ✅ | ✅ | ✅ |
| Create draft transaction | ❌ | ✅ | ✅ | ✅ |
| Edit draft transaction | ❌ | ✅ (own) | ✅ | ✅ |
| Delete draft transaction | ❌ | ✅ (own) | ✅ | ✅ |
| Submit transaction for approval | ❌ | ✅ | ✅ (auto-approved) | ✅ |
| Bulk submit transactions | ❌ | ✅ | ✅ | ✅ |
| Cancel draft transaction | ❌ | ✅ (own) | ✅ | ✅ |
| Uncancel draft transaction | ❌ | ✅ (own) | ✅ | ✅ |
| View pending approval queue | ❌ | ❌ | ✅ | ✅ |
| **Approve transaction** | ❌ | ❌ | ✅ | ✅ |
| **Disapprove/Return to draft** | ❌ | ❌ | ✅ | ✅ |
| **Unlock approved transaction** | ❌ | ❌ | ❌ | ✅ |
| Request change to posted record | ❌ | ✅ | ✅ | ✅ |
| Approve change request | ❌ | ❌ | ✅ | ✅ |
| **Deposits** |
| Create deposit | ❌ | ✅ | ✅ | ✅ |
| Submit deposit | ❌ | ✅ (needs approval) | ✅ (auto-approved) | ✅ |
| Approve deposit | ❌ | ❌ | ✅ | ✅ |
| Reject deposit | ❌ | ❌ | ✅ | ✅ |
| Cancel draft deposit | ❌ | ✅ | ✅ | ✅ |
| Request deposit change | ❌ | ✅ | ✅ | ✅ |
| Request deposit cancellation | ❌ | ✅ | ✅ | ✅ |
| **Fund Accountability** |
| Create fund received/disbursed | ❌ | ✅ | ✅ | ✅ |
| Request fund cancellation | ❌ | ✅ (pending approval) | ✅ (direct) | ✅ (direct) |
| Approve fund cancellation | ❌ | ❌ | ✅ | ✅ |
| Reject fund cancellation | ❌ | ❌ | ✅ | ✅ |
| **Petty Cash** |
| Create petty cash voucher | ❌ | ✅ | ✅ | ✅ |
| Submit voucher | ❌ | ✅ | ✅ | ✅ |
| Post voucher | ❌ | ❌ | ✅ | ✅ |
| Cancel voucher | ❌ | ✅ (draft/submitted) | ✅ | ✅ |
| **Collections** |
| Create collection | ❌ | ✅ | ✅ | ✅ |
| Submit collection | ❌ | ✅ | ✅ | ✅ |
| Approve collection | ❌ | ❌ | ✅ | ✅ |
| Reject collection | ❌ | ❌ | ✅ | ✅ |
| **Reports** |
| View reports | ✅ | ✅ | ✅ | ✅ |
| Export reports | ✅ | ✅ | ✅ | ✅ |
| Daily sales report | ✅ | ✅ | ✅ | ✅ |
| Sales summary report | ✅ | ✅ | ✅ | ✅ |
| Deposit report | ✅ | ✅ | ✅ | ✅ |
| Trial balance | ✅ | ✅ | ✅ | ✅ |
| **User Management** |
| View user list | ❌ | ❌ | ✅ | ✅ |
| Create new user | ❌ | ❌ | ✅ | ✅ |
| Edit user details | ❌ | ❌ | ✅ | ✅ |
| Activate/deactivate user | ❌ | ❌ | ✅ | ✅ |
| Assign module roles | ❌ | ❌ | ✅ | ✅ |
| Grant Admin status | ❌ | ❌ | ✅ | ✅ |
| **Grant SuperUser status** | ❌ | ❌ | ❌ | ✅ |
| Change user password | ❌ | ❌ | ✅ | ✅ |
| **Demote Admin** | ❌ | ❌ | ❌ | ✅ |
| Modify protected accounts | ❌ | ❌ | ❌ | ✅ (except "admin") |
| **Register/Master Files** |
| View master files | ✅ | ✅ | ✅ | ✅ |
| Create/edit customers | ❌ | ✅ | ✅ | ✅ |
| Create/edit vendors | ❌ | ✅ | ✅ | ✅ |
| Create/edit products | ❌ | ✅ | ✅ | ✅ |
| Configure tender types | ❌ | ✅ | ✅ | ✅ |
| Configure transaction types | ❌ | ✅ | ✅ | ✅ |
| **Accounting** |
| Chart of accounts | ✅ | ✅ | ✅ | ✅ |
| Post journal entries | ❌ | ❌ | ✅ | ✅ |
| Approve journal entries | ❌ | ❌ | ✅ | ✅ |

---

## 4. Database Schema

### User Table

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    user_name VARCHAR,           -- Unique username (e.g., "jsmith")
    pass_word VARCHAR,           -- Hashed password
    first_name VARCHAR,
    middle_name VARCHAR,
    last_name VARCHAR,
    email VARCHAR,

    -- Permission Flags (Boolean)
    superuser BOOLEAN DEFAULT 0, -- SuperUser privileges
    admin BOOLEAN DEFAULT 0,     -- Admin/approval authority
    staff BOOLEAN DEFAULT 0,     -- Staff/data entry
    active BOOLEAN DEFAULT 0,    -- Account enabled

    salt VARCHAR                 -- Password salt
);
```

### Role Table

```sql
CREATE TABLE role (
    id INTEGER PRIMARY KEY,
    role_name VARCHAR            -- e.g., "Daily Sales", "user"
);
```

### UserRole Junction Table

```sql
CREATE TABLE user_role (
    user_id INTEGER,
    role_id INTEGER,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (role_id) REFERENCES role(id)
);
```

### Relationships

```
User (1) ──────< (N) UserRole (N) >────── (1) Role
     └─ roles backref               └─ users backref
```

**Query Examples:**

```python
# Get user's module roles
user.user_roles  # Returns ['Daily Sales', 'user', 'Customer']

# Get users with a specific role
role = Role.query.filter_by(role_name='Daily Sales').first()
users_with_daily_sales = [ur.user for ur in role.users]

# Check if user has role
if 'Daily Sales' in current_user.user_roles:
    # Show Daily Sales menu
```

---

## 5. User Management Interface

### 5.1 User List (`/user/list`)

**Access:** Requires `user` role

**Features:**
- Lists all users in system
- Shows username, full name, status flags
- Links to user detail/role management

### 5.2 User Group Management (`/user/user_group/<user_id>`)

**Access:** Requires `user` role + Admin privileges

**Features:**
- View user details
- Toggle permission flags:
  - ✅/❌ SuperUser (SuperUser only)
  - ✅/❌ Admin
  - ✅/❌ Staff
  - ✅/❌ Active
- Assign/remove module roles (checkboxes)
- Organized by category (Operations, Accounting, Register, System)
- Shows count: "15/30 roles assigned"

**Protected Actions:**
- Master "admin" account cannot be modified
- Non-SuperUsers cannot grant SuperUser status
- Admins cannot be demoted (safety protection)

### 5.3 Toggle Routes

| Route | Purpose | Access |
|-------|---------|--------|
| `/user/user_admin` | Toggle Admin flag | Admin+ |
| `/user/user_superuser` | Toggle SuperUser flag | SuperUser only |
| `/user/user_staff` | Toggle Staff flag | Admin+ |
| `/user/user/active` | Toggle Active flag | Admin+ |
| `/user/add_role` | Assign module role | Admin+ |
| `/user/remove_role` | Remove module role | Admin+ |

### 5.4 Password Management

**Change Password (`/user/change_password`)**
- Admin can change any user's password
- Requires admin privileges
- Uses salted password hashing (werkzeug)

**Password Security:**
```python
# Password is salted and hashed
salt = os.urandom(16)
salted_password = f"{salt}{password}"
hashed = generate_password_hash(salted_password)

# Verification
def check_pass_word(self, password):
    salted = f"{self.salt}{password}"
    return check_password_hash(self.pass_word, salted)
```

---

## 6. Special Accounts

### 6.1 Master "admin" Account

**Username:** `admin`

**Special Properties:**
- Created during first user registration
- Always has:
  - `superuser = True`
  - `admin = True`
  - `active = True`
  - All module roles assigned
- **Cannot be modified** by any user (hardcoded protection)
- Cannot have flags toggled
- Cannot be deleted
- Cannot have "user" role removed

**Code Protection:**

```python
# In user management routes
if user.user_name == "admin":
    flash("Cannot change the master admin account.", category="error")
    return redirect(...)
```

**Purpose:**
- System recovery account
- Ensures always one SuperUser exists
- Cannot be locked out

### 6.2 First User Registration

When system is first deployed:

1. First user registers with username "admin"
2. Automatically granted:
   - `superuser=True`
   - `admin=True`
   - `active=True`
3. All roles automatically assigned
4. This account becomes permanent master admin

**Code:**

```python
if form.user_name == "admin":
    user.active = True
    user.superuser = True
    user.admin = True
```

---

## 7. Permission Enforcement Patterns

### 7.1 Decorator-Based Enforcement

**Login Required:**

```python
from application.blueprints.user.views import login_required

@bp.route('/some_page')
@login_required
def some_page():
    # User must be logged in and active
    ...
```

**Role-Based Access:**

```python
from application.blueprints.user.views import roles_accepted

@bp.route('/daily_sales')
@login_required
@roles_accepted(['Daily Sales'])  # Must have this module role
def daily_sales_home():
    ...
```

**User Type Enforcement:**

From `permissions.py`:

```python
from application.blueprints.operations.daily_sales.permissions import (
    superuser_required,
    admin_required,
    staff_required,
    view_required
)

@bp.route('/approve')
@login_required
@roles_accepted(['Daily Sales'])
@admin_required  # Admin or SuperUser
def approve_transaction():
    ...
```

### 7.2 Inline Permission Checks

**Common Pattern:**

```python
# SuperUser only
if not current_user.superuser:
    abort(403)

# Admin or SuperUser
if not (current_user.admin or current_user.superuser):
    abort(403)

# Staff or higher
if not (current_user.staff or current_user.admin or current_user.superuser):
    abort(403)
```

### 7.3 Template-Level Enforcement

**Hide UI elements based on permissions:**

```html
{% if current_user.admin or current_user.superuser %}
<button>Approve</button>
{% endif %}

{% if "Daily Sales" in current_user.user_roles %}
<a href="{{ url_for('daily_sales.home') }}">Daily Sales</a>
{% endif %}
```

### 7.4 Hierarchical Permission Helpers

From `permissions.py`:

```python
def is_admin(user=None):
    """Check if user is Admin or SuperUser"""
    if user is None:
        user = get_current_user()
    return user and (user.is_admin or user.is_superuser)

def is_staff(user=None):
    """Check if user is Staff (or higher)"""
    return user and (user.is_staff or user.is_admin or user.is_superuser)

def can_approve_submissions(user=None):
    """Admin or SuperUser can approve"""
    return is_admin(user)
```

**Usage:**

```python
from application.blueprints.operations.daily_sales.permissions import (
    can_approve_submissions
)

if can_approve_submissions():
    # Show approval button
```

---

## 8. Security Analysis

### 8.1 Strengths

✅ **Layered Security:**
- Login authentication (Flask-Login)
- Active status check
- Module role check
- User type permission check
- Template-level hiding

✅ **Password Security:**
- Salted passwords (random 16-byte salt)
- Werkzeug password hashing (PBKDF2)
- Salt stored separately

✅ **Protected Master Account:**
- "admin" account cannot be locked out
- Hardcoded protections prevent modification
- Ensures system recovery possible

✅ **Hierarchical Permissions:**
- Clear escalation: View < Staff < Admin < SuperUser
- Principle of least privilege
- Granular control per module

✅ **Audit Trail Integration:**
- User ID stored in created_by, approved_by fields
- Disapproval reasons logged with admin name
- Timestamp tracking

### 8.2 Potential Vulnerabilities

⚠️ **No Password Complexity Requirements:**
- No minimum length enforcement
- No complexity rules (uppercase, numbers, symbols)
- User can set weak password

**Recommendation:** Add password validation:
```python
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    # ...
```

⚠️ **No Account Lockout:**
- Unlimited login attempts
- No brute-force protection
- No CAPTCHA

**Recommendation:** Implement login attempt tracking:
```python
class User(db.Model):
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
```

⚠️ **No Password Expiration:**
- Passwords never expire
- No forced rotation policy

**Recommendation:** For compliance, add:
```python
password_changed_at = db.Column(db.DateTime)
password_expires_days = 90  # Configurable
```

⚠️ **No Session Timeout:**
- Sessions persist indefinitely
- No inactivity timeout

**Recommendation:** Configure Flask session timeout:
```python
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
```

⚠️ **No Two-Factor Authentication (2FA):**
- Single-factor authentication only
- Higher risk for admin accounts

**Recommendation:** Add TOTP-based 2FA for admin/superuser accounts.

⚠️ **Role Assignment Not Logged:**
- No audit trail when roles are granted/revoked
- Cannot track who made user an admin

**Recommendation:** Create UserRoleAudit table:
```python
class UserRoleAudit(db.Model):
    action = 'granted'|'revoked'
    role_name = 'admin'|'superuser'|'staff'
    performed_by_id
    performed_at
```

⚠️ **Email Not Verified:**
- Email address stored but not validated
- No email verification process

**Recommendation:** Add email verification token system.

### 8.3 Attack Surface Analysis

**Low Risk:**
- ✅ SQL Injection: Using SQLAlchemy ORM (parameterized queries)
- ✅ XSS: Flask auto-escaping in templates
- ✅ CSRF: Flask-WTF token protection

**Medium Risk:**
- ⚠️ Brute Force: No rate limiting or lockout
- ⚠️ Session Hijacking: No session timeout
- ⚠️ Privilege Escalation: Multiple permission checks prevent

**High Risk (if deployed without HTTPS):**
- 🔴 Password Transmission: Must use HTTPS
- 🔴 Session Cookie Theft: Requires secure cookies

**Recommendations for Production:**
```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # JavaScript cannot access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
```

---

## 9. Usage Examples

### 9.1 Creating a New User (Admin Task)

**Scenario:** Hire new cashier "Maria Santos"

**Steps:**

1. **Admin registers user:**
   - Navigate to `/user/register`
   - Enter:
     - Username: `msantos`
     - Password: (set temporary password)
     - First Name: Maria
     - Last Name: Santos
     - Email: maria.santos@healthcollective.com
   - Submit
   - User created with `active=False` (default)

2. **Admin activates and assigns permissions:**
   - Navigate to `/user/list`
   - Click on Maria Santos
   - Toggle `Active` = ON
   - Toggle `Staff` = ON
   - Assign module roles:
     - ✅ Daily Sales
     - ✅ Customer
     - ✅ Collections
   - Save

3. **Maria logs in:**
   - Username: `msantos`
   - Password: (temporary)
   - Changes password via `/user/change_password`

4. **Maria's capabilities:**
   - ✅ Can see Daily Sales, Customer, Collections menus
   - ✅ Can create draft transactions
   - ✅ Can submit transactions
   - ❌ Cannot approve transactions (not admin)
   - ❌ Cannot see user management (no "user" role)

---

### 9.2 Promoting Staff to Admin

**Scenario:** Promote "Juan Cruz" from Staff to Admin

**Steps:**

1. **Admin navigates to user management:**
   - `/user/user_group/<juan_id>`

2. **Toggle Admin flag:**
   - Click "Admin" toggle
   - Route: `/user/user_admin?user_id=<juan_id>&value=1`
   - Flash: "Administrator status enabled for jcruz"

3. **Juan's new capabilities:**
   - ✅ All previous Staff capabilities (inherits)
   - ✅ Can now approve submitted transactions
   - ✅ Can view pending approval queues
   - ✅ Can disapprove/return to draft
   - ✅ Can manage users
   - ✅ Can approve change requests

4. **Protection:**
   - ⚠️ Juan's admin status cannot be revoked (safety protection)
   - Only SuperUser can demote Juan

---

### 9.3 Creating SuperUser (Restricted)

**Scenario:** Grant SuperUser to IT Administrator "Alice Wang"

**Steps:**

1. **Existing SuperUser logs in** (only SuperUser can grant SuperUser)

2. **Navigate to user management:**
   - `/user/user_group/<alice_id>`

3. **Toggle SuperUser flag:**
   - Click "SuperUser" toggle
   - Route: `/user/user_superuser?user_id=<alice_id>&value=1`
   - Flash: "SuperUser status enabled for awang"

4. **Alice's capabilities:**
   - ✅ All Admin capabilities (inherits)
   - ✅ Can unlock approved transactions
   - ✅ Can grant SuperUser to others
   - ✅ Can demote admins (except master "admin")
   - ✅ Can direct edit posted records

---

### 9.4 View-Only User

**Scenario:** External auditor "Robert Lee" needs read-only access

**Steps:**

1. **Admin creates user:**
   - Username: `rlee`
   - Active = ON
   - Staff = OFF
   - Admin = OFF
   - SuperUser = OFF

2. **Assign view roles:**
   - ✅ Trial Balance
   - ✅ Ledger
   - ✅ Daily Sales (read-only)

3. **Robert's capabilities:**
   - ✅ Can view reports
   - ✅ Can export data
   - ✅ Can see dashboards
   - ❌ Cannot create/edit anything
   - ❌ Cannot submit or approve

---

## 10. Recommendations

### 10.1 Immediate Improvements

**Priority: HIGH**

1. **Add Password Complexity Requirements**
   - Minimum 8 characters
   - Require uppercase, lowercase, number
   - Block common passwords

2. **Implement Account Lockout**
   - Lock after 5 failed attempts
   - 15-minute lockout period
   - Email notification to user

3. **Add Session Timeout**
   - 8-hour session lifetime
   - Warn user 5 minutes before expiration

4. **Enable Secure Cookie Flags**
   - `SESSION_COOKIE_SECURE = True` (HTTPS)
   - `SESSION_COOKIE_HTTPONLY = True`
   - `SESSION_COOKIE_SAMESITE = 'Lax'`

### 10.2 Medium-Term Enhancements

**Priority: MEDIUM**

5. **Add Role Assignment Audit Log**
   - Track who granted/revoked permissions
   - Timestamp all changes
   - Alert on suspicious activity

6. **Implement Password Expiration**
   - 90-day rotation for admin accounts
   - 180-day for staff accounts
   - Warning before expiration

7. **Add Email Verification**
   - Send verification token on registration
   - Require email confirmation before activation

8. **Create User Activity Log**
   - Track logins, logouts
   - Track permission changes
   - Track sensitive actions (approvals, deletions)

### 10.3 Long-Term Strategic

**Priority: LOW**

9. **Two-Factor Authentication (2FA)**
   - TOTP-based (Google Authenticator)
   - Required for admin/superuser accounts
   - Optional for staff

10. **Single Sign-On (SSO)**
    - Integrate with corporate identity provider
    - OAuth 2.0 / SAML support
    - Centralized user management

11. **Role-Based Access Control (RBAC) Enhancement**
    - Move from boolean flags to true RBAC
    - Define permissions at granular level
    - Separate "role" from "permission"

12. **IP Whitelisting**
    - Restrict admin access to office IPs
    - VPN requirement for remote access

### 10.4 Documentation Improvements

13. **Create User Permission Guide**
    - Document each user type's capabilities
    - Create decision tree for role assignment
    - Provide training materials

14. **Create Security Policy Document**
    - Password requirements
    - Account management procedures
    - Incident response plan

15. **Create User Onboarding Checklist**
    - Steps for creating new user
    - Required training
    - Access review schedule

---

## Summary Statistics

### User Types
- **4 Permission Levels:** SuperUser, Admin, Staff, View
- **Hierarchical Inheritance:** Each level inherits lower privileges

### Module Roles
- **30+ Modules:** Organized across 4 categories
- **Granular Access Control:** Per-module visibility

### Protected Elements
- **1 Master Account:** "admin" (cannot be modified)
- **Admin Demotion Protection:** Admins cannot be demoted by other admins

### Security Features
- ✅ Salted password hashing
- ✅ SQLAlchemy ORM (SQL injection prevention)
- ✅ Flask CSRF protection
- ✅ Template auto-escaping (XSS prevention)
- ✅ Hierarchical permission checks
- ⚠️ No 2FA
- ⚠️ No account lockout
- ⚠️ No session timeout

---

## Conclusion

The Health Collective Inc. uses a **robust dual-layer permission system** combining user type flags (SuperUser/Admin/Staff) with module-based role assignments. This provides both hierarchical authority (who can approve) and feature access control (what modules are visible).

**Strengths:**
- Clear permission hierarchy
- Granular module access
- Protected master account
- Secure password handling
- Comprehensive audit capabilities

**Areas for Improvement:**
- Password complexity enforcement
- Account lockout mechanism
- Session timeout
- Two-factor authentication
- Role assignment audit logging

The system is well-designed for a healthcare operations management application, with appropriate separation of concerns between data entry staff, approval authorities, and system administrators.

---

**END OF REPORT**

*For questions or clarification, refer to:*
- [User Model](application/blueprints/user/models.py)
- [User Views](application/blueprints/user/views.py)
- [Permissions Module](application/blueprints/operations/daily_sales/permissions.py)
