#!/usr/bin/env python
"""
Database Schema Consistency Check

Compares the actual database schema in instance folder with SQLAlchemy model definitions
to identify any mismatches or inconsistencies.

Usage: python scripts/database/check_schema_consistency.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from application import create_app
from application.extensions import db
from sqlalchemy import inspect, text

app = create_app()

def get_database_tables():
    """Get all tables from the actual database."""
    inspector = inspect(db.engine)
    return inspector.get_table_names()

def get_database_columns(table_name):
    """Get columns from actual database table."""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    return {col['name']: {
        'type': str(col['type']),
        'nullable': col['nullable'],
        'default': col['default']
    } for col in columns}

def get_model_tables():
    """Get all tables from SQLAlchemy models."""
    return [table.name for table in db.metadata.sorted_tables]

def get_model_columns(table_name):
    """Get columns from SQLAlchemy model."""
    table = db.metadata.tables.get(table_name)
    if table is None:
        return {}

    return {col.name: {
        'type': str(col.type),
        'nullable': col.nullable,
        'default': str(col.default) if col.default else None
    } for col in table.columns}

def check_consistency():
    """Check consistency between database and models."""
    print("=" * 80)
    print("DATABASE SCHEMA CONSISTENCY CHECK")
    print("=" * 80)
    print()

    # Get tables
    db_tables = set(get_database_tables())
    model_tables = set(get_model_tables())

    print(f"Database tables: {len(db_tables)}")
    print(f"Model tables: {len(model_tables)}")
    print()

    # Tables only in database
    db_only = db_tables - model_tables
    if db_only:
        print("WARNING: TABLES IN DATABASE BUT NOT IN MODELS:")
        for table in sorted(db_only):
            print(f"   - {table}")
        print()

    # Tables only in models
    model_only = model_tables - db_tables
    if model_only:
        print("WARNING: TABLES IN MODELS BUT NOT IN DATABASE:")
        for table in sorted(model_only):
            print(f"   - {table}")
        print()

    # Check columns for common tables
    common_tables = db_tables & model_tables
    mismatches = []

    print(f"Checking {len(common_tables)} common tables...")
    print()

    for table_name in sorted(common_tables):
        db_cols = get_database_columns(table_name)
        model_cols = get_model_columns(table_name)

        db_col_names = set(db_cols.keys())
        model_col_names = set(model_cols.keys())

        # Columns only in database
        db_col_only = db_col_names - model_col_names
        if db_col_only:
            mismatches.append({
                'table': table_name,
                'type': 'columns_in_db_not_in_model',
                'columns': db_col_only
            })

        # Columns only in model
        model_col_only = model_col_names - db_col_names
        if model_col_only:
            mismatches.append({
                'table': table_name,
                'type': 'columns_in_model_not_in_db',
                'columns': model_col_only
            })

        # Check column type mismatches for common columns
        common_cols = db_col_names & model_col_names
        type_mismatches = []

        for col_name in common_cols:
            db_type = db_cols[col_name]['type']
            model_type = model_cols[col_name]['type']

            # Normalize types for comparison
            db_type_norm = db_type.replace('VARCHAR', 'TEXT').replace('INTEGER', 'INT')
            model_type_norm = model_type.replace('VARCHAR', 'TEXT').replace('INTEGER', 'INT')

            if db_type_norm != model_type_norm:
                type_mismatches.append({
                    'column': col_name,
                    'db_type': db_type,
                    'model_type': model_type
                })

        if type_mismatches:
            mismatches.append({
                'table': table_name,
                'type': 'type_mismatch',
                'details': type_mismatches
            })

    # Report mismatches
    if mismatches:
        print("SCHEMA MISMATCHES FOUND:")
        print()

        for mismatch in mismatches:
            table = mismatch['table']
            mtype = mismatch['type']

            if mtype == 'columns_in_db_not_in_model':
                print(f"Table: {table}")
                print(f"  Issue: Columns exist in DATABASE but not in MODEL")
                for col in sorted(mismatch['columns']):
                    print(f"    - {col}")
                print()

            elif mtype == 'columns_in_model_not_in_db':
                print(f"Table: {table}")
                print(f"  Issue: Columns exist in MODEL but not in DATABASE")
                for col in sorted(mismatch['columns']):
                    print(f"    - {col}")
                print()

            elif mtype == 'type_mismatch':
                print(f"Table: {table}")
                print(f"  Issue: Column type mismatches")
                for detail in mismatch['details']:
                    col = detail['column']
                    db_type = detail['db_type']
                    model_type = detail['model_type']
                    print(f"    - {col}: DB={db_type} vs Model={model_type}")
                print()

        print("=" * 80)
        print("RECOMMENDATION: Create a migration to fix schema mismatches")
        print("Run: flask db migrate -m 'Fix schema mismatches'")
        print("=" * 80)
        return False
    else:
        print("SUCCESS: NO SCHEMA MISMATCHES FOUND")
        print()
        print("Database schema is consistent with SQLAlchemy models.")
        print("=" * 80)
        return True

if __name__ == '__main__':
    with app.app_context():
        try:
            consistent = check_consistency()
            sys.exit(0 if consistent else 1)
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(2)
