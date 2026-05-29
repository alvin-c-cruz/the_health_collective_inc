# Utility Scripts

This directory contains utility scripts organized by purpose. **Never commit .py files to the root directory** - they belong here.

## Directory Structure

```
scripts/
├── README.md (this file)
├── migrations/       # Database migration helpers
├── data-cleanup/     # Data deletion utilities
├── database/         # Database inspection tools
├── testing/          # Testing utilities
└── imports/          # Data import scripts (gitignored)
```

## `migrations/`
Database migration helper scripts. Run these when you need to apply custom migrations or seed data.

**Examples:**
- `run_migration.py` - Apply pending Alembic migrations
- `run_audit_log_migration.py` - Migrate audit log data
- `run_cancellation_migration.py` - Apply cancellation workflow migration

## `data-cleanup/`
Data deletion and cleanup utilities. Use these for clearing test data or resetting specific tables.

**⚠️ WARNING:** These scripts permanently delete data. Always backup before running.

**Examples:**
- `clear_all_test_data.py` - Remove all test data
- `delete_records.py` - Interactive record deletion
- `clear_daily_sales_data.py` - Clear daily sales transactions
- `clear_collections_data.py` - Clear collections data

## `database/`
Database inspection and analysis tools. Use these to examine schema, data, or generate reports.

**Examples:**
- `database_summary.py` - Generate database statistics
- `examine_models.py` - Inspect SQLAlchemy models
- `examine_daily_sales.py` - Analyze daily sales data
- `add_daily_sales_indexes.py` - Add database indexes

## `testing/`
Testing utilities and helper scripts. Generate test checklists, run test suites, verify fixes.

**Examples:**
- `create_testing_checklist.py` - Generate testing documentation
- `test_financial_statements_fix.py` - Verify financial report fixes

## `imports/` (gitignored)
Scripts for importing data from Excel and other sources. These are kept locally but not committed.

**Examples:**
- `import_sales_preview.py` - Preview and parse Excel transactions
- `commit_transactions.py` - Initial transaction import
- `reimport_all_transactions.py` - Complete re-import with fixes

## Usage Guidelines

1. **Always run scripts from the project root:**
   ```bash
   python scripts/database/database_summary.py
   ```

2. **Scripts require Flask app context:**
   Most scripts use `create_app()` to access database and models.

3. **Check script documentation:**
   Read the docstring at the top of each script before running.

4. **Never commit to root:**
   New utility scripts must go in the appropriate subdirectory.
   The pre-commit hook will reject root directory scripts.

## Adding New Scripts

When creating a new utility script:

1. Choose the correct subdirectory based on purpose
2. Add a clear docstring explaining what it does
3. Include usage instructions and warnings
4. Never place it in the root directory
5. The pre-commit hook will enforce this rule

## Automated Enforcement

A pre-commit hook prevents clutter in the root directory:
- ✅ Allows only essential files in root (`flask_app.py`, docs)
- ❌ Rejects .py and .md files that don't belong in root
- 📝 Provides helpful error messages with correct locations

## Questions?

See [CLAUDE.md](../CLAUDE.md) for complete file organization rules.
