#!/usr/bin/env python
"""
Clear all AdminTransaction records (unapprove all transactions for testing)
"""
from application import create_app
from application.extensions import db
from application.blueprints.operations.daily_sales.admin_models import AdminTransaction

app = create_app()

with app.app_context():
    print("Clearing AdminTransaction records...")

    # Count current records
    count = AdminTransaction.query.count()
    print(f"Found {count} approval record(s)")

    if count == 0:
        print("No records to delete.")
    else:
        # Delete all approval records
        AdminTransaction.query.delete()
        db.session.commit()
        print(f"[OK] Deleted {count} approval record(s)")
        print("\nAll transactions are now in 'Pending Approval' status (if they were submitted)")
