"""
Clear all data from daily sales models
"""
from application import create_app
from application.extensions import db
from application.blueprints.operations.daily_sales.models import (
    Transaction, TransactionDetail, TransactionTender,
    Deposit, DepositItem,
    FundReceived, FundDisbursed,
    PettyCashVoucher, ReimbursementReport, ReimbursementReceived
)
from application.blueprints.operations.daily_sales.admin_models import (
    AdminTransaction, UserTransaction
)
from application.blueprints.operations.daily_sales.audit_models import AuditLog

# Set up Flask app context
app = create_app()

with app.app_context():
    # Delete in order respecting foreign key constraints

    print("Deleting audit logs...")
    count = AuditLog.query.filter_by(record_type='transaction').delete()
    print(f"  Deleted {count} audit log entries")

    print("Deleting reimbursement received records...")
    count = ReimbursementReceived.query.delete()
    print(f"  Deleted {count} reimbursement received records")

    print("Deleting petty cash vouchers...")
    count = PettyCashVoucher.query.delete()
    print(f"  Deleted {count} petty cash vouchers")

    print("Deleting reimbursement reports...")
    count = ReimbursementReport.query.delete()
    print(f"  Deleted {count} reimbursement reports")

    print("Deleting fund disbursed records...")
    count = FundDisbursed.query.delete()
    print(f"  Deleted {count} fund disbursed records")

    print("Deleting fund received records...")
    count = FundReceived.query.delete()
    print(f"  Deleted {count} fund received records")

    print("Deleting deposit items...")
    count = DepositItem.query.delete()
    print(f"  Deleted {count} deposit items")

    print("Deleting deposits...")
    count = Deposit.query.delete()
    print(f"  Deleted {count} deposits")

    print("Deleting admin transactions (approvals)...")
    count = AdminTransaction.query.delete()
    print(f"  Deleted {count} admin transaction records")

    print("Deleting user transactions (preparers)...")
    count = UserTransaction.query.delete()
    print(f"  Deleted {count} user transaction records")

    print("Deleting transaction tenders...")
    count = TransactionTender.query.delete()
    print(f"  Deleted {count} transaction tenders")

    print("Deleting transaction details...")
    count = TransactionDetail.query.delete()
    print(f"  Deleted {count} transaction details")

    print("Deleting transactions...")
    count = Transaction.query.delete()
    print(f"  Deleted {count} transactions")

    db.session.commit()

    print("\nAll daily sales data cleared successfully!")
    print("Database is now clean and ready for fresh data.")
