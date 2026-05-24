"""
Detailed database summary
"""
from application import create_app
from application.extensions import db
from sqlalchemy import text

# Set up Flask app context
app = create_app()

with app.app_context():
    print("=" * 80)
    print("DATABASE SUMMARY - db.sqlite3")
    print("=" * 80)
    print()

    # Categories
    categories = {
        "USERS & PERMISSIONS": [
            'user', 'role', 'user_role'
        ],
        "CHART OF ACCOUNTS": [
            'account', 'account_class', 'account_type',
            'user_account', 'user_account_class', 'user_account_type', 'admin_account'
        ],
        "MASTER DATA": [
            'customer', 'vendor', 'product', 'product_type', 'company',
            'tender', 'sex', 'transaction_type', 'fund_category', 'bank_account',
            'ape_batch', 'measure', 'payee'
        ],
        "DAILY SALES TRANSACTIONS": [
            'transaction', 'transaction_detail', 'transaction_tender',
            'user_transaction', 'admin_transaction',
            'deposit', 'deposit_item',
            'fund_received', 'fund_disbursed',
            'petty_cash_voucher', 'reimbursement_report', 'reimbursement_received'
        ],
        "ACCOUNTING BOOKS": [
            'sales', 'sales_detail', 'sales_extra', 'sales_extra_detail',
            'receipt', 'receipt_detail', 'receipt_extra', 'receipt_extra_detail',
            'disbursement', 'disbursement_detail', 'disbursement_extra', 'disbursement_extra_detail',
            'general', 'general_detail', 'general_extra', 'general_extra_detail',
            'accounts_payable', 'accounts_payable_detail', 'accounts_payable_extra', 'accounts_payable_extra_detail'
        ],
        "COLLECTIONS": [
            'collection', 'collection_detail'
        ],
        "AUDIT & CHANGE TRACKING": [
            'audit_log', 'change_request'
        ],
        "SYSTEM": [
            'alembic_version'
        ]
    }

    total_records = 0

    for category, tables in categories.items():
        print(f"\n{category}")
        print("-" * 80)

        category_total = 0
        for table in tables:
            try:
                if table == 'transaction':
                    # Handle reserved keyword
                    result = db.session.execute(text('SELECT COUNT(*) FROM "transaction"'))
                else:
                    result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                category_total += count

                if count > 0:
                    print(f"  + {table:<45} {count:>10,} records")
                else:
                    print(f"    {table:<45} {count:>10} records")
            except Exception as e:
                print(f"    {table:<45} (table not found)")

        print(f"  {'SUBTOTAL':<45} {category_total:>10,} records")
        total_records += category_total

    print()
    print("=" * 80)
    print(f"TOTAL RECORDS IN DATABASE: {total_records:,}")
    print("=" * 80)
    print()
    print("NOTES:")
    print("  + Tables with data")
    print("    Empty tables")
    print("=" * 80)
