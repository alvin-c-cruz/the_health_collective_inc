"""
Examine all models and count records
"""
from application import create_app
from application.extensions import db

# Set up Flask app context
app = create_app()

with app.app_context():
    # Get all tables from database
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()

    print("=" * 80)
    print("DATABASE RECORD COUNTS")
    print("=" * 80)
    print()

    # Sort tables alphabetically
    tables.sort()

    total_records = 0

    for table_name in tables:
        try:
            result = db.session.execute(db.text(f"SELECT COUNT(*) FROM {table_name}"))
            count = result.scalar()
            total_records += count

            # Print with formatting
            status = "+" if count > 0 else " "
            print(f"{status} {table_name:<40} {count:>10,} records")

        except Exception as e:
            print(f"- {table_name:<40} Error: {str(e)}")

    print()
    print("=" * 80)
    print(f"TOTAL RECORDS ACROSS ALL TABLES: {total_records:,}")
    print("=" * 80)
