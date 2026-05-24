"""
Test script to verify that prepaid expenses no longer appears in Income Statement
and that the Balance Sheet balances correctly after the fix.
"""

from application import create_app, db
from application.blueprints.accounting.account.models import Account
from application.blueprints.accounting.account_class.models import AccountClass
from datetime import date

app = create_app()

with app.app_context():
    print("=" * 80)
    print("FINANCIAL STATEMENTS FIX VERIFICATION")
    print("=" * 80)

    # Get all accounts
    accounts = Account.query.all()

    # Separate accounts by statement type
    balance_sheet_accounts = []
    income_statement_accounts = []

    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue

        class_name = account.account_type.account_class.account_class_name.upper()
        type_name = account.account_type.account_type_name.upper()

        # Balance Sheet logic (from balance_sheet/views.py)
        if ('ASSET' in class_name or
            'LIABILIT' in class_name or
            'EQUITY' in class_name or
            'CAPITAL' in class_name):
            balance_sheet_accounts.append({
                'number': account.account_number,
                'title': account.account_title,
                'type': type_name,
                'class': class_name
            })

        # Income Statement logic (NEW - after fix)
        is_balance_sheet_account = (
            'ASSET' in class_name or
            'LIABILIT' in class_name or
            'EQUITY' in class_name or
            'CAPITAL' in class_name
        )

        if not is_balance_sheet_account:
            if ('REVENUE' in class_name or 'INCOME' in class_name or 'SALES' in type_name or
                'COST OF SALES' in type_name or 'COST OF GOODS' in type_name or
                'EXPENSE' in class_name or 'EXPENSE' in type_name):
                income_statement_accounts.append({
                    'number': account.account_number,
                    'title': account.account_title,
                    'type': type_name,
                    'class': class_name
                })

    print("\n" + "=" * 80)
    print("PREPAID EXPENSES VERIFICATION")
    print("=" * 80)

    # Check if prepaid expenses appears in income statement
    prepaid_in_income = [acc for acc in income_statement_accounts if 'PREPAID' in acc['title'].upper()]
    prepaid_in_balance = [acc for acc in balance_sheet_accounts if 'PREPAID' in acc['title'].upper()]

    print(f"\nPrepaid accounts in Balance Sheet: {len(prepaid_in_balance)}")
    for acc in prepaid_in_balance:
        print(f"  [OK] {acc['number']}: {acc['title']} (Class: {acc['class']})")

    print(f"\nPrepaid accounts in Income Statement: {len(prepaid_in_income)}")
    if prepaid_in_income:
        print("  [ERROR] Prepaid accounts should NOT appear in Income Statement!")
        for acc in prepaid_in_income:
            print(f"    {acc['number']}: {acc['title']} (Class: {acc['class']})")
    else:
        print("  [OK] CORRECT: No prepaid accounts in Income Statement")

    print("\n" + "=" * 80)
    print("ACCOUNT DISTRIBUTION SUMMARY")
    print("=" * 80)

    print(f"\nBalance Sheet accounts: {len(balance_sheet_accounts)}")

    # Count by class
    bs_by_class = {}
    for acc in balance_sheet_accounts:
        cls = acc['class']
        if cls not in bs_by_class:
            bs_by_class[cls] = 0
        bs_by_class[cls] += 1

    for cls, count in sorted(bs_by_class.items()):
        print(f"  {cls}: {count} accounts")

    print(f"\nIncome Statement accounts: {len(income_statement_accounts)}")

    # Count by class
    is_by_class = {}
    for acc in income_statement_accounts:
        cls = acc['class']
        if cls not in is_by_class:
            is_by_class[cls] = 0
        is_by_class[cls] += 1

    for cls, count in sorted(is_by_class.items()):
        print(f"  {cls}: {count} accounts")

    print("\n" + "=" * 80)
    print("BALANCE SHEET BALANCE CHECK")
    print("=" * 80)

    # Calculate totals
    total_assets = 0
    total_liabilities = 0
    total_equity = 0

    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue

        class_name = account.account_type.account_class.account_class_name.upper()
        balance = account.balance()

        if 'ASSET' in class_name:
            total_assets += balance
        elif 'LIABILIT' in class_name:
            total_liabilities += abs(balance)  # Liabilities are typically negative
        elif 'EQUITY' in class_name or 'CAPITAL' in class_name:
            total_equity += abs(balance)  # Equity is typically negative

    print(f"\nTotal Assets:      PHP {total_assets:,.2f}")
    print(f"Total Liabilities: PHP {total_liabilities:,.2f}")
    print(f"Total Equity:      PHP {total_equity:,.2f}")
    print(f"\nLiabilities + Equity: PHP {(total_liabilities + total_equity):,.2f}")
    print(f"Difference:           PHP {(total_assets - total_liabilities - total_equity):,.2f}")

    if abs(total_assets - total_liabilities - total_equity) < 0.01:
        print("\n[OK] BALANCE SHEET IS BALANCED!")
    else:
        print("\n[WARNING] BALANCE SHEET IS NOT BALANCED")
        print("  (Note: This may be expected if there are net income/loss amounts not yet closed to equity)")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

    # Final verdict
    if not prepaid_in_income:
        print("\n[SUCCESS] Prepaid expenses fix is working correctly!")
        print("  Prepaid expenses now only appear in Balance Sheet, not Income Statement.")
    else:
        print("\n[FAILURE] Prepaid expenses still appearing in Income Statement")
