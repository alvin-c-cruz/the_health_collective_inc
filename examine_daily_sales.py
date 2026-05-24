"""
Examine daily sales models specifically
"""
from application import create_app
from application.blueprints.operations.daily_sales.models import (
    Transaction, TransactionDetail, TransactionTender,
    Deposit, DepositItem,
    FundReceived, FundDisbursed, FundCategory,
    PettyCashVoucher, Payee, ReimbursementReport, ReimbursementReceived
)
from application.blueprints.operations.daily_sales.admin_models import (
    AdminTransaction, UserTransaction
)
from application.blueprints.operations.daily_sales.audit_models import AuditLog
from application.blueprints.operations.daily_sales.change_request_models import ChangeRequest

# Set up Flask app context
app = create_app()

with app.app_context():
    print("=" * 80)
    print("DAILY SALES MODELS - RECORD COUNTS")
    print("=" * 80)
    print()

    models = [
        ("Transaction", Transaction),
        ("TransactionDetail", TransactionDetail),
        ("TransactionTender", TransactionTender),
        ("AdminTransaction (Approvals)", AdminTransaction),
        ("UserTransaction (Preparers)", UserTransaction),
        ("Deposit", Deposit),
        ("DepositItem", DepositItem),
        ("FundCategory", FundCategory),
        ("FundReceived", FundReceived),
        ("FundDisbursed", FundDisbursed),
        ("PettyCashVoucher", PettyCashVoucher),
        ("Payee", Payee),
        ("ReimbursementReport", ReimbursementReport),
        ("ReimbursementReceived", ReimbursementReceived),
        ("ChangeRequest", ChangeRequest),
        ("AuditLog", AuditLog),
    ]

    total = 0
    for name, model in models:
        count = model.query.count()
        total += count
        status = "+" if count > 0 else " "
        print(f"{status} {name:<40} {count:>10,} records")

    print()
    print("=" * 80)
    print(f"TOTAL DAILY SALES RECORDS: {total:,}")
    print("=" * 80)
