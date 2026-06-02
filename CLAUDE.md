# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Running the Application

```bash
# Start Flask development server
python flask_app.py
```

Application runs on `http://localhost:9000` (or your machine's IP on port 9000).

The server auto-reloads on file changes in development mode.

## Database Migrations

```bash
# Create migration after model changes
flask db migrate -m "Description of changes"

# Apply migrations to database
flask db upgrade

# Rollback last migration
flask db downgrade

# Show migration history
flask db history
```

**Note**: Database file is `the_health_collective_inc.db` in the project root (automatically named from `COMPANY_NAME` in config).

## Key Architecture

### Blueprint Pattern

Every module follows this structure:
```
application/blueprints/{category}/{module_name}/
├── __init__.py          # Exports app_name, app_label, menu_label, bp, Model
├── models.py            # SQLAlchemy models (Obj, ObjUser, ObjAdmin)
├── forms.py             # Flask-WTF forms
├── views.py             # Flask routes (bp Blueprint)
├── admin_models.py      # Admin interface (legacy, being phased out)
└── pages/               # Jinja2 templates
    └── {module_name}/
        ├── home.html    # List view
        └── form.html    # Add/edit form
```

**Blueprint Registration**: Automatic via `application/__init__.py`
- Discovers all modules with `bp` attribute in `blueprints/__init__.py`
- Registers blueprints automatically
- Builds menu from `menu_label` tuples: `(app_name, url_prefix, display_label)`

### Role-Based Access Control

Authentication uses `@login_required` and `@roles_accepted([role_names])` decorators:

```python
from application.blueprints.user import login_required, roles_accepted

@bp.route("/")
@login_required
@roles_accepted(["Account"])  # Role name from app_label
def home():
    # ...
```

**Role Management**:
- Roles sync automatically on app startup from registered blueprints
- Each blueprint's `app_label` becomes a role name
- Roles are grouped in navbar: Operations, Accounting, Register, System
- User-role mapping in `UserRole` junction table

### Versioning System

Version displayed in navbar: `v1.0.{commit_count}[-dirty]`

Powered by `application/utils/version.py`:
- Counts git commits for patch version
- Adds `-dirty` suffix if uncommitted changes exist
- Falls back to `v1.0.dev` if git unavailable
- Cached on first call for performance

### Philippine Timezone & Date Utilities

Application uses Philippine time (`Asia/Manila`, UTC+8):

```python
from application.extensions import ph_today, year_first_day, month_first_day

today = ph_today()  # Returns date object in PH timezone
```

Utility functions in `application/extensions.py`:
- `ph_today()` - Current PH date
- `year_first_day()` - First day of current year
- `month_first_day()` - First day of current month
- `year_last_day()` - Last day of current year
- `month_last_day()` - Last day of current month
- `next_control_number(obj, field, date)` - Auto-increment document numbers
- `long_date(str_date)` - Format as "January 01, 2026"
- `short_date(str_date)` - Format as "01-Jan-2026"

### Configuration

Instance configuration at `instance/config.py`:
- `COMPANY_NAME` - Company name (used for database naming)
- `SECRET_KEY` - Flask secret key
- `SQLALCHEMY_DATABASE_URI` - Database connection (auto-generated from company name)
- `CSRF_TOKEN_NAME`, `CSRF_TOKEN_BYTES` - CSRF settings

Database file name is auto-generated: Company name → lowercase → remove special chars → replace spaces with underscores.

---

## File Organization

### **Rule: Keep the root directory clean**

The root directory should only contain essential project files. This makes the codebase easier to navigate and maintain.

**Root Directory - Allowed Files:**
- `flask_app.py` - Main application entry point
- `CLAUDE.md` - AI development guide
- `DESIGN_SYSTEM.md` - Design system specification
- `DESIGN_TOKENS_USAGE.md` - Token usage guide
- `FEATURES.md` - Feature documentation
- `MARKETING_CONSTRUCTION.md` - Current marketing materials
- Standard project files (`.gitignore`, `requirements.txt`, `README.md`, etc.)

**Root Directory - NOT Allowed:**
- ❌ Client-specific proposals or documents
- ❌ Temporary analysis reports
- ❌ Conversion instructions
- ❌ Old bug reports or implementation summaries
- ❌ Migration summaries (use `docs/migration-history/` instead)
- ❌ Utility scripts (use `scripts/` subdirectories instead)
- ❌ Data cleanup scripts
- ❌ Testing scripts
- ❌ Database utility scripts

**Process for Documentation:**
1. **Analysis reports** - Create in root during work, then move to `docs/` when complete
2. **Migration summaries** - Move to `docs/migration-history/` after migration is done
3. **Client documents** - Create outside the repository, never commit
4. **Temporary files** - Remove immediately when no longer needed

**Subdirectories for Documentation:**
- `docs/` - Technical documentation, architecture notes, user guides
- `docs/migration-history/` - Historical migration summaries (archived)

**Subdirectories for Scripts:**
- `scripts/migrations/` - Database migration scripts (Alembic helpers)
- `scripts/data-cleanup/` - Data deletion and cleanup utilities
- `scripts/database/` - Database inspection and utility scripts
- `scripts/testing/` - Testing utilities and checklist generators

### **Automated Enforcement - Pre-commit Hook**

A pre-commit hook automatically enforces these rules:

**What it does:**
- ✅ Allows only essential files in root directory
- ❌ Rejects commits with .py or .md files that don't belong in root
- 📝 Shows helpful error messages with correct directory locations
- 🚫 Prevents accidental clutter before it gets committed

**Setup (automatic):**
The pre-commit hook is already installed at `.git/hooks/pre-commit`. It runs automatically on every commit.

**If you need to reinstall:**
```bash
chmod +x .git/hooks/pre-commit
```

**Example rejection message:**
```
❌ ERROR: Root directory clutter detected!

The following files should NOT be in the root directory:
  - test_script.py
  - analysis_notes.md

Please move them to appropriate directories:
  • Python scripts (.py):
    - scripts/migrations/     (database migration helpers)
    - scripts/data-cleanup/   (data deletion utilities)
    - scripts/database/       (database inspection tools)
    - scripts/testing/        (testing utilities)

  • Markdown files (.md):
    - docs/                   (technical documentation)
    - docs/migration-history/ (migration summaries)

Commit rejected. Please reorganize files and try again.
```

**Note to Claude:** When creating new utility scripts or documentation, always place them in the correct subdirectory from the start. The pre-commit hook will prevent root directory clutter automatically.

---

## Design System

### **Rule: All UI must use design system tokens**

Before creating or modifying any UI, read [`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md). All UI must use the tokens defined there — **no hardcoded colors, font sizes, spacing values, or radii**. Use semantic token names (e.g. `bg-surface`, not `bg-white`).

**Examples:**

✅ **Good** - Using design tokens:
```html
<div style="background: var(--thc-bg-surface); padding: var(--thc-padding-card);
            border-radius: var(--thc-radius-xl); box-shadow: var(--thc-shadow-sm);">
```

❌ **Bad** - Hardcoded values:
```html
<div style="background: #ffffff; padding: 24px; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
```

✅ **Good** - Using utility classes:
```html
<div class="bg-surface rounded-xl shadow-sm">
```

### **Rule: No one-off styles**

If a needed pattern doesn't exist in the design system, **stop and propose an addition to `DESIGN_SYSTEM.md` before implementing it**. Do not invent one-off styles.

**Process:**
1. Check `DESIGN_SYSTEM.md` for existing tokens
2. Check `DESIGN_TOKENS_USAGE.md` for usage examples
3. If pattern doesn't exist, ask the user to approve adding it to the design system
4. Once approved, document the new token/pattern
5. Then implement it

### **Reference Implementation**

Use `application/blueprints/dashboard/pages/dashboard/home.html` as the canonical example of layout density, spacing rhythm, and component composition. New pages should feel like they belong next to it.

**What to match:**
- Layout density (how much content per screen)
- Spacing rhythm (vertical spacing between sections)
- Component composition (how elements are grouped)
- Visual hierarchy (heading sizes, emphasis)
- Interactive patterns (hover states, transitions)

---

## When Building UI

### **1. Reuse Existing Components**

**Always check `application/templates/components/` for existing reusable components before creating new ones.**

**Before creating a new component, check:**
- `application/templates/components/` - **Reusable UI components (CHECK HERE FIRST)**
- `application/templates/` - Base templates and macros
- `application/templates/macros_button.html` - Button macros
- `application/templates/macros_simple_form.html` - Form field macros
- `application/templates/macros_form_header.html` - Form header layouts
- `application/templates/macros_form_detail.html` - Form detail sections
- Blueprint-specific templates in `application/blueprints/*/pages/`

### **2. Create Reusable Components**

If you create a new component, place it in `application/templates/components/` and make it **reusable, not page-specific**.

**Component Guidelines:**
- Make it generic and configurable via parameters
- Use Jinja2 macros for reusable UI components
- Accept design tokens as parameters (don't hardcode)
- Document parameters and usage examples
- Follow existing macro patterns in `application/templates/macros_*.html`

**Example of a good reusable component:**
```jinja2
{% macro card(title, variant="default", size="md") %}
<div class="card card-{{ size }}{% if variant != 'default' %} card-{{ variant }}{% endif %}">
  {% if title %}
  <div class="card-header">{{ title }}</div>
  {% endif %}
  <div class="card-body">
    {{ caller() }}
  </div>
</div>
{% endmacro %}
```

### **3. Match Existing Patterns**

Match the existing patterns for **loading states, empty states, and error states**.

**Loading States:**
```html
<!-- Example: Check existing templates for spinner/loading patterns -->
<div class="loading-spinner">
  <i class="bi bi-hourglass-split"></i> Loading...
</div>
```

**Empty States:**
```html
<!-- Example: Check existing templates for empty state patterns -->
<div class="text-center text-muted py-4">
  No records found.
</div>
```

**Error States:**
```html
<!-- Example: Check existing templates for error patterns -->
<div class="alert alert-danger">
  {{ error_message }}
</div>
```

---

## Technology Stack Reference

This is a Flask application with:
- **Backend**: Flask 3.1.0, SQLAlchemy 2.0.36, Flask-Migrate 4.1.0
- **Frontend**: Bootstrap 5 (local), Bootstrap Icons, Jinja2 templates
- **Fonts**: Playfair Display (headings), Inter (body), DM Mono (numbers)
- **Styling**: CSS variables (design system tokens) + utility classes
- **Database**: SQLite (`the_health_collective_inc.db`)

See [`CLAUDE.md`](CLAUDE.md) in the original instructions for detailed architecture notes.

---

## Key Conventions

### Typography
```css
/* Use semantic tokens */
font-size: var(--thc-body-size);      /* 14px - body text */
font-size: var(--thc-h2-size);        /* 24px - section headings */
font-size: var(--thc-label-size);     /* 12px - labels */
font-family: var(--thc-font-body);    /* Inter */
font-family: var(--thc-font-mono);    /* DM Mono - for numbers */
```

### Colors
```css
/* Use semantic aliases */
background: var(--thc-bg-surface);      /* White - cards */
color: var(--thc-text-primary);         /* Dark gray - main text */
color: var(--thc-text-secondary);       /* Medium gray - muted text */
border-color: var(--thc-border-default);/* Light gray - borders */

/* Use semantic color scales */
background: var(--thc-primary-600);     /* Brand color */
background: var(--thc-success-600);     /* Green - approvals */
background: var(--thc-danger-600);      /* Red - destructive */
```

### Spacing
```css
/* Use spacing scale (4px grid) */
padding: var(--thc-padding-card);       /* 24px - cards */
padding: var(--thc-padding-button);     /* 8px 20px - buttons */
gap: var(--thc-gap-md);                 /* 12px - flexbox/grid gaps */
margin-bottom: var(--thc-stack-md);     /* 20px - vertical spacing */
```

### Components
```css
/* Buttons */
.btn-primary {
  background: var(--thc-primary-600);
  padding: var(--thc-padding-button);
  border-radius: var(--thc-radius-md);
}

/* Cards */
.card {
  background: var(--thc-bg-surface);
  border: 1px solid var(--thc-border-default);
  border-radius: var(--thc-radius-xl);
  padding: var(--thc-padding-card);
  box-shadow: var(--thc-shadow-sm);
}

/* Forms */
.form-control {
  padding: var(--thc-padding-input);
  border: 1px solid var(--thc-border-strong);
  border-radius: var(--thc-radius-md);
}
```

---

## Documentation References

- **[`DESIGN_SYSTEM.md`](DESIGN_SYSTEM.md)** - Complete design system specification
- **[`DESIGN_TOKENS_USAGE.md`](DESIGN_TOKENS_USAGE.md)** - How to use design tokens
- **[`docs/migration-history/IMPLEMENTATION_SUMMARY.md`](docs/migration-history/IMPLEMENTATION_SUMMARY.md)** - Token implementation status
- **[`docs/ui-audit.md`](docs/ui-audit.md)** - Original UI audit
- **`application/static/css/design-system.css`** - Token definitions (source of truth)
- **`application/static/css/design-system-test.html`** - Visual token reference

---

## Checklist for New UI

Before submitting UI changes, verify:

- [ ] All colors use design system tokens (no hex values)
- [ ] All spacing uses design system tokens (no arbitrary px/rem)
- [ ] All font sizes use design system tokens
- [ ] All border radius uses design system tokens
- [ ] All shadows use design system tokens
- [ ] Reused existing components where possible
- [ ] New components are generic and reusable
- [ ] Matches existing patterns for loading/empty/error states
- [ ] Matches reference implementation for visual consistency
- [ ] Responsive on mobile (uses Bootstrap breakpoints)
- [ ] Accessible (proper contrast, focus states)

---

## Common Mistakes to Avoid

❌ **Don't**: Use arbitrary spacing
```html
<div style="padding: 18px; margin-bottom: 22px;">
```

✅ **Do**: Use spacing tokens
```html
<div style="padding: var(--thc-space-5); margin-bottom: var(--thc-stack-md);">
```

---

❌ **Don't**: Hardcode colors
```html
<button style="background: #1a6473; color: white;">
```

✅ **Do**: Use color tokens
```html
<button style="background: var(--thc-primary-600); color: var(--thc-text-inverse);">
```

---

❌ **Don't**: Mix units inconsistently
```html
<div style="padding: 16px 1rem; gap: 12px;">
```

✅ **Do**: Use consistent tokens
```html
<div style="padding: var(--thc-space-4); gap: var(--thc-gap-md);">
```

---

❌ **Don't**: Create page-specific components
```jinja2
{% macro dashboard_metric_card_only_for_home_page() %}
```

✅ **Do**: Create generic reusable components
```jinja2
{% macro metric_card(label, value, icon=None, variant="default") %}
```

---

## Questions?

- Check `DESIGN_TOKENS_USAGE.md` for token examples
- View `design-system-test.html` for visual reference
- Ask the user if you need clarification on design patterns
- Propose additions to the design system if patterns are missing

---

**Last Updated**: 2026-05-29
**Design System Version**: 2.0
