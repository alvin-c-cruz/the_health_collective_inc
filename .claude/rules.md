# Claude Code Rules & Procedures for The Health Collective Inc

## Project Information

- **Project Name:** The Health Collective Inc (THCI)
- **Developer:** Alvin Cruz, CPA
- **Project Path:** `c:\envs\the_health_collective_inc`
- **Framework:** Flask 3.0+ with SQLAlchemy 2.0
- **Database:** SQLite (`instance/the_health_collective_inc.db`)
- **Server:** Flask development server on port 9000 (http://192.168.68.109:9000)
- **Related Projects:** `cebu_landmasters`, `acas` (Alvin's own accounting system)

## Version Control Rules

### **Semantic Versioning (MAJOR.MINOR.PATCH)**

Format: `thci X.Y.Z`

- **MAJOR (X)** - Breaking changes, major redesigns
  - Complete database structure changes
  - Removing features entirely
  - Fundamental workflow changes
  - Example: `1.4.2` → `2.0.0`

- **MINOR (Y)** - New features (backwards-compatible)
  - Adding new functionality
  - New reports or modules
  - Significant UI improvements
  - Example: `1.4.2` → `1.5.0`
  - Reset PATCH to 0 when incrementing MINOR

- **PATCH (Z)** - Bug fixes only
  - Fixing calculation errors
  - Correcting display issues
  - Small corrections
  - Example: `1.4.2` → `1.4.3`

**When to Increment:**
- ✅ Increment MINOR version at end of session when new features are added
- ✅ Increment PATCH version immediately after bug fixes
- ✅ Increment MAJOR version only when explicitly decided by developer
- ✅ Update version in navbar.html: `<span class="navbar-version ms-auto">thci X.Y.Z</span>`

**Current Version:** `thci 1.4.0` (as of 2026-05-19)

## Git Workflow Rules

### **CRITICAL RULE: Auto-commit After Each Task**
- ✅ **MUST** execute `git commit` automatically after EVERY successful task completion
- ✅ Commit immediately when a feature/fix is complete
- ✅ Use descriptive commit messages following the project's style
- ✅ Always include the Claude Code footer:
  ```
  🤖 Generated with [Claude Code](https://claude.com/claude-code)

  Co-Authored-By: Claude <noreply@anthropic.com>
  ```

### Files to Exclude from Git
- `application/database.db` - Database file (should be in .gitignore)
- `migrate_*.py` - One-time migration scripts
- `update_*.py` - One-time update scripts
- `*.pyc` - Python bytecode
- `__pycache__/` - Python cache directories
- `venv/` - Virtual environment

### Commit Message Format
```
<Short descriptive title>

<Detailed explanation of changes>
- Bullet points for key features
- Technical details
- Behavior changes

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Coding Standards

### Currency Formatting
- **ALWAYS** use Philippine standard format: `#,##0.00`
- **Template format:** `₱{{ "{:,.2f}".format(amount) }}`
- **Never use:** `₱{{ "%.2f"|format(amount) }}` (missing thousand separators)

### User Role Hierarchy
1. **SuperUser** - Highest level, can delegate all roles including other SuperUsers
2. **Admin** - Can approve submissions/change requests, "admin" user is protected from demotion
3. **Staff** - Can create transactions (draft/submitted), request changes, view reports
4. **View** - Read-only access to reports, no CRUD operations

### Transaction Workflow States
- **Draft** - Editable by creator
- **Submitted** - Awaiting approval
- **Posted** - Approved and locked
- **Cancelled** - Soft-deleted (data intact, can be un-cancelled before submission)

### Change Request Workflow
- Staff can request changes to **posted** transactions
- Admin reviews and approves/rejects change requests
- Full audit trail with JSON-based old/new value tracking
- Change history visible per transaction

## File Structure Conventions

### Blueprint Pattern
```
application/
├── blueprints/
│   ├── operations/
│   │   └── daily_sales/
│   │       ├── __init__.py
│   │       ├── models.py          # Database models
│   │       ├── views.py           # Route handlers
│   │       ├── forms.py           # Form classes
│   │       ├── permissions.py     # Role-based access control
│   │       └── pages/
│   │           └── daily_sales/
│   │               └── *.html     # Jinja2 templates
│   └── user/
│       ├── models.py
│       ├── views.py
│       └── pages/
│           └── user/
│               └── *.html
```

### Naming Conventions
- **Routes:** Use kebab-case in URLs (`/transaction/<id>/request-change`)
- **Functions:** Use snake_case (`def request_transaction_change()`)
- **Classes:** Use PascalCase (`class ChangeRequest`)
- **Templates:** Use snake_case (`change_requests.html`)
- **CSS Classes:** Use kebab-case with THCI prefix (`thc-metric-val`)

## Design System (THCI Style)

### Colors
```css
--thc-primary: #185FA5       /* Primary blue */
--thc-primary-light: #e8f1f8 /* Light blue background */
--thc-primary-hover: #0f4880 /* Darker blue for hover */
--thc-accent: #1a7a60        /* Accent green */
--thc-accent-hover: #145a48  /* Darker green */
--thc-danger: #b91c1c        /* Red for errors/cancel */
--thc-danger-light: #fef2f2  /* Light red background */
--thc-text: #1f2937          /* Dark gray text */
--thc-text-muted: #6b7280    /* Muted gray text */
--thc-border: #d1d5db        /* Border gray */
```

### Button Classes
- `btn-save` - Teal/accent color for Save Draft
- `btn-submit` - Blue for Submit actions
- `btn-back` - Gray outline for Cancel/Back
- `btn-danger-outline` - Red outline for destructive actions
- `btn-success-outline` - Green outline for restore actions

### Typography
- **Font Heading:** 'DM Sans', sans-serif
- **Font Body:** 'DM Sans', sans-serif
- **Font Mono:** 'DM Mono', monospace (for currency/numbers)

## Database Conventions

### Audit Trail Fields (Standard Pattern)
```python
created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
created_by_user = db.relationship('User', foreign_keys=[created_by_id])
created_at = db.Column(db.DateTime, default=datetime.utcnow)

submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
submitted_by_user = db.relationship('User', foreign_keys=[submitted_by_id])
submitted_at = db.Column(db.DateTime, nullable=True)

approved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
approved_by_user = db.relationship('User', foreign_keys=[approved_by_id])
approved_at = db.Column(db.DateTime, nullable=True)
```

### Legacy Field Handling
- Keep legacy fields for backward compatibility during migrations
- Add comments to distinguish new vs legacy fields
- Example:
  ```python
  # Legacy flags (keep for backward compatibility)
  admin = db.Column(db.Boolean(), default=False)
  staff = db.Column(db.Boolean(), default=False)

  # New role flags (current system)
  is_superuser = db.Column(db.Boolean(), default=False)
  is_admin = db.Column(db.Boolean(), default=False)
  ```

## Permission System

### Permission Check Functions
```python
def is_superuser(user=None):
    """Check if user is a SuperUser"""

def is_admin(user=None):
    """Check if user is Admin or SuperUser"""

def is_staff(user=None):
    """Check if user is Staff, Admin, or SuperUser"""

def can_view(user=None):
    """Check if user has view access"""
```

### Permission Decorators
```python
@superuser_required  # Only SuperUser
@admin_required      # Admin or SuperUser
@staff_required      # Staff, Admin, or SuperUser
@view_required       # Any authenticated user with view access
```

## Testing Procedures

### Before Committing
1. ✅ Verify Flask server is running without errors
2. ✅ Check server logs for any warnings/errors
3. ✅ Test the specific feature implemented
4. ✅ Verify backward compatibility (existing features still work)

### After Major Changes
1. ✅ Review all modified routes
2. ✅ Test user role permissions
3. ✅ Check database integrity
4. ✅ Verify UI renders correctly

## Common Patterns

### Flash Message Categories
- `success` - Green, successful operations
- `warning` - Yellow/orange, warnings
- `danger` - Red, errors or destructive actions
- `info` - Blue, informational messages

### Form Submission Pattern
```python
if request.method == 'POST':
    # Validate input
    # Process data
    # Update database
    db.session.commit()
    flash('Success message', 'success')
    return redirect(url_for('blueprint.route'))
```

### Query Pattern with User Context
```python
from flask import session
user_id = session.get('user_id')
current_user_obj = User.query.get(user_id) if user_id else None

# Use current_user_obj for permission checks
if not current_user_obj or not current_user_obj.is_admin:
    flash('Access denied.', 'danger')
    return redirect(url_for('dashboard.home'))
```

## Important Notes

### Philippine Timezone
- Database stores UTC times
- Display in Asia/Manila (UTC+8) when needed
- Use `datetime.utcnow()` for database storage

### Protected Users
- User "admin" (id=1) is protected from demotion
- User "admin" has both `is_superuser=True` and `is_admin=True`
- Cannot modify own user account in user management

### Change Request System
- Only for **posted** transactions
- JSON serialization for old/new values
- Three statuses: `pending`, `approved`, `rejected`, `direct`
- Full audit trail with reason and review notes

## Task Management

### Using TodoWrite Tool
- ✅ Always use TodoWrite for multi-step tasks
- ✅ Update status in real-time (pending → in_progress → completed)
- ✅ Mark tasks complete IMMEDIATELY after finishing
- ✅ Only ONE task should be in_progress at a time

### Task Description Format
```json
{
  "content": "Fix authentication bug",
  "activeForm": "Fixing authentication bug",
  "status": "in_progress"
}
```

## Background Servers

Current running servers:
- `the_health_collective_inc` - Port 9000 (http://192.168.68.109:9000)
- `product_costing` - (port unknown, check with user)

Check server logs periodically for errors using BashOutput tool.

---

**Last Updated:** 2026-05-19
**Updated By:** Claude Code with Alvin Cruz
