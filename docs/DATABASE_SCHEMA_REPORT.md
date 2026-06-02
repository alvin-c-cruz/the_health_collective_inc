# Database Schema Consistency Report

**Generated:** 2026-06-02
**Database:** `instance/the_health_collective_inc.db`
**Status:** ⚠️ Schema Inconsistencies Found

---

## Executive Summary

The database schema has **4 obsolete columns** in the `user` table that need to be removed. These columns were likely from an older version of the application and are no longer used by the current SQLAlchemy models.

---

## Findings

### 1. Tables Overview

- **Database Tables:** 98
- **Model Tables:** 97
- **Missing in Models:** 1 table (`alembic_version` - expected, this is for migrations)
- **Missing in Database:** 0 tables

### 2. Schema Mismatches

#### User Table - Obsolete Columns

The `user` table contains **duplicate columns** that are obsolete:

| Obsolete Column (DB) | Current Column (Model) | Purpose |
|---------------------|------------------------|---------|
| `is_superuser` | `superuser` | Superuser flag |
| `is_admin` | `admin` | Admin flag |
| `is_staff` | `staff` | Staff flag |
| `is_view` | `active` | View/Active flag |

**Root Cause:**
The User model (lines 54-71 in `application/blueprints/user/models.py`) defines `is_superuser`, `is_admin`, `is_staff`, and `is_view` as **@property methods** that map to the actual database columns (`superuser`, `admin`, `staff`, `active`).

However, the database still contains old columns with the `is_*` names from a previous schema version.

**Current Model Definition:**
```python
class User(db.Model):
    # Actual database columns
    superuser = db.Column(db.Boolean(), default=False)
    admin = db.Column(db.Boolean(), default=False)
    staff = db.Column(db.Boolean(), default=False)
    active = db.Column(db.Boolean(), default=False)

    # Properties that reference the columns above
    @property
    def is_superuser(self):
        return self.superuser if self.superuser is not None else False

    @property
    def is_admin(self):
        return self.admin if self.admin is not None else False

    # ... etc
```

**Actual Database Schema:**
```
user table columns:
  id                   INTEGER
  user_name            VARCHAR
  pass_word            VARCHAR
  # ... other columns ...
  admin                BOOLEAN         ← Current model column
  staff                BOOLEAN         ← Current model column
  active               BOOLEAN         ← Current model column
  superuser            BOOLEAN         ← Current model column
  is_superuser         BOOLEAN         ← OBSOLETE (duplicate)
  is_admin             BOOLEAN         ← OBSOLETE (duplicate)
  is_staff             BOOLEAN         ← OBSOLETE (duplicate)
  is_view              BOOLEAN         ← OBSOLETE (duplicate)
```

---

## Impact Assessment

### Current Impact: LOW

- ✅ Application is **functioning correctly** using the current model columns
- ✅ Obsolete columns are **not referenced** by any code
- ⚠️ Database has **redundant columns** that waste space
- ⚠️ Schema inconsistency may **confuse developers** or **cause issues** with future migrations

### Potential Risks:

1. **Alembic Migrations:** Future auto-generated migrations may try to add these columns again
2. **Database Size:** Wasted space (minimal, but poor practice)
3. **Confusion:** New developers may wonder which columns to use
4. **Data Integrity:** If old columns have different values, could cause confusion

---

## Recommendations

### Option 1: Create Migration to Remove Obsolete Columns (Recommended)

Create an Alembic migration to drop the unused columns:

```bash
flask db migrate -m "Remove obsolete is_* columns from user table"
```

This will generate a migration file. Review it to ensure it drops these columns:
- `is_superuser`
- `is_admin`
- `is_staff`
- `is_view`

Then apply the migration:
```bash
flask db upgrade
```

**Pros:**
- Clean schema
- Proper migration history
- Reversible if needed

**Cons:**
- Requires testing
- Must coordinate with any running deployments

### Option 2: Manual Database Cleanup

Directly modify the database (NOT recommended for production):

```sql
ALTER TABLE user DROP COLUMN is_superuser;
ALTER TABLE user DROP COLUMN is_admin;
ALTER TABLE user DROP COLUMN is_staff;
ALTER TABLE user DROP COLUMN is_view;
```

**Pros:**
- Quick fix

**Cons:**
- No migration history
- Not reversible
- Alembic may get confused

### Option 3: Do Nothing (Not Recommended)

Leave the obsolete columns in place.

**Pros:**
- No work required
- No risk of breaking anything

**Cons:**
- Schema remains inconsistent
- Technical debt accumulates
- May cause issues with future migrations

---

## Action Plan

### Immediate Actions (Recommended)

1. ✅ **Create backup of database**
   ```bash
   cp instance/the_health_collective_inc.db instance/the_health_collective_inc.db.backup
   ```

2. ✅ **Create migration**
   ```bash
   flask db migrate -m "Remove obsolete is_* columns from user table"
   ```

3. ✅ **Review generated migration**
   - Check `migrations/versions/` for the new migration file
   - Verify it drops only the obsolete columns
   - Ensure it doesn't affect current columns

4. ✅ **Test migration in development**
   ```bash
   flask db upgrade
   python scripts/database/check_schema_consistency.py
   ```

5. ✅ **Verify application still works**
   - Test user login
   - Test role-based permissions
   - Test admin/superuser functions

6. ✅ **Commit migration to repository**
   ```bash
   git add migrations/
   git commit -m "migration: Remove obsolete is_* columns from user table"
   git push
   ```

### Long-term Actions

1. **Update pre-commit hook** to run schema consistency check (optional)
2. **Add schema validation to CI/CD** if applicable
3. **Document migration strategy** for future schema changes

---

## Verification

After applying the migration, run the consistency check again:

```bash
python scripts/database/check_schema_consistency.py
```

Expected output:
```
SUCCESS: NO SCHEMA MISMATCHES FOUND

Database schema is consistent with SQLAlchemy models.
```

---

## Additional Notes

### alembic_version Table

The `alembic_version` table appearing in the database but not in models is **expected and normal**. This table is managed by Alembic (Flask-Migrate) to track which migrations have been applied.

### Schema Consistency Check Script

A new utility script has been created at:
```
scripts/database/check_schema_consistency.py
```

This script can be run anytime to verify database schema matches the SQLAlchemy models.

---

## Questions?

- Review the User model: `application/blueprints/user/models.py`
- Check Alembic migrations: `migrations/versions/`
- See Flask-Migrate docs: https://flask-migrate.readthedocs.io/

---

**Report Generated By:** Schema Consistency Check Script
**Script Location:** `scripts/database/check_schema_consistency.py`
**Last Updated:** 2026-06-02
