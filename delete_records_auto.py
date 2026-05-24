#!/usr/bin/env python
"""
Delete All Records Script (Auto-confirm)
Deletes all records from: Customer (patients), Product, Deposit, Collection tables

WARNING: This will permanently delete ALL data from these tables!
         This action cannot be undone unless you have a database backup.

Usage: python delete_records_auto.py
"""

import sys
from flask import Flask
from application import create_app
from application.extensions import db

# Import models
from application.blueprints.register.customer.models import Customer
from application.blueprints.register.product.models import Product
from application.blueprints.operations.daily_sales.models import (
    Deposit, DepositItem, Transaction, TransactionDetail, TransactionTender
)
from application.blueprints.operations.collections.models import (
    Collection, CollectionDetail
)

def count_records():
    """Count current records before deletion"""
    counts = {
        'customers': Customer.query.count(),
        'products': Product.query.count(),
        'deposits': Deposit.query.count(),
        'deposit_items': DepositItem.query.count(),
        'collections': Collection.query.count(),
        'collection_details': CollectionDetail.query.count(),
        'transactions': Transaction.query.count(),
        'transaction_details': TransactionDetail.query.count(),
        'transaction_tenders': TransactionTender.query.count(),
    }
    return counts

def delete_all_records():
    """Delete all records from specified tables in correct order"""

    print("\n" + "="*70)
    print("DELETE ALL RECORDS - The Health Collective Inc.")
    print("="*70)
    print("\nDeleting ALL data from:")
    print("  - Customers (Patients)")
    print("  - Products")
    print("  - Deposits (and related items)")
    print("  - Collections (and related details)")
    print("  - Transactions (and related details/tenders)")

    # Count current records
    print("\nCurrent record counts:")
    counts = count_records()
    for table, count in counts.items():
        print(f"  {table:25} {count:6,} records")

    total_records = sum(counts.values())
    print(f"\n  {'TOTAL':25} {total_records:6,} records will be deleted")

    if total_records == 0:
        print("\n✓ No records to delete. Tables are already empty.")
        return

    print("\n" + "="*70)
    print("Starting deletion process...")
    print("="*70 + "\n")

    try:
        # Delete in correct order to avoid foreign key violations
        # Child tables first, then parent tables

        # 1. Collection Details (child of Collection)
        print("Deleting CollectionDetail records...")
        count = CollectionDetail.query.delete()
        print(f"  [OK] Deleted {count:,} collection detail records")

        # 2. Collections (references Transactions via TransactionTender)
        print("Deleting Collection records...")
        count = Collection.query.delete()
        print(f"  [OK] Deleted {count:,} collection records")

        # 3. Deposit Items (child of Deposit, references Transaction)
        print("Deleting DepositItem records...")
        count = DepositItem.query.delete()
        print(f"  [OK] Deleted {count:,} deposit item records")

        # 4. Deposits
        print("Deleting Deposit records...")
        count = Deposit.query.delete()
        print(f"  [OK] Deleted {count:,} deposit records")

        # 5. Transaction Tenders (child of Transaction)
        print("Deleting TransactionTender records...")
        count = TransactionTender.query.delete()
        print(f"  [OK] Deleted {count:,} transaction tender records")

        # 6. Transaction Details (child of Transaction, references Product)
        print("Deleting TransactionDetail records...")
        count = TransactionDetail.query.delete()
        print(f"  [OK] Deleted {count:,} transaction detail records")

        # 7. Transactions (references Customer)
        print("Deleting Transaction records...")
        count = Transaction.query.delete()
        print(f"  [OK] Deleted {count:,} transaction records")

        # 8. Products (now safe to delete)
        print("Deleting Product records...")
        count = Product.query.delete()
        print(f"  [OK] Deleted {count:,} product records")

        # 9. Customers (Patients) (now safe to delete)
        print("Deleting Customer (Patient) records...")
        count = Customer.query.delete()
        print(f"  [OK] Deleted {count:,} customer records")

        # Commit all deletions
        print("\nCommitting changes to database...")
        db.session.commit()

        print("\n" + "="*70)
        print("[SUCCESS] All records deleted successfully!")
        print("="*70)

        # Verify deletion
        print("\nVerification - Current record counts:")
        final_counts = count_records()
        for table, count in final_counts.items():
            status = "[OK]" if count == 0 else "[WARN]"
            print(f"  {status} {table:25} {count:6,} records")

        if sum(final_counts.values()) == 0:
            print("\n[OK] All specified tables are now empty.")
        else:
            print("\n[WARN] Some records remain. Check for foreign key issues.")

    except Exception as e:
        db.session.rollback()
        print("\n" + "="*70)
        print("[ERROR] Deletion failed!")
        print("="*70)
        print(f"\nError message: {str(e)}")
        print("\nChanges have been rolled back. No data was deleted.")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    # Create Flask app context
    app = create_app()

    with app.app_context():
        delete_all_records()
