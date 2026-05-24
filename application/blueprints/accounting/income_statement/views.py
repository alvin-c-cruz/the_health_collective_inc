from flask import Blueprint, render_template, request, send_file
from flask_login import login_required
from datetime import date, datetime, timedelta
import pandas as pd
import io

from .. account import Account
from .. account_type import AccountType
from .. account_class import AccountClass


bp = Blueprint("income_statement", __name__, template_folder="pages", url_prefix="/income_statement")


@bp.route("/", methods=["GET"])
@login_required
def home():
    """
    Income Statement - Statement of Comprehensive Income
    Shows Revenue, Expenses, and Net Income for a date range
    """
    # Get date parameters (support both 'date' and 'to_date')
    today = date.today()
    date_param = request.args.get('date')

    if date_param:
        # If 'date' parameter is provided (from modal), use it as to_date and calculate from_date as beginning of year
        try:
            to_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            from_date = date(to_date.year, 1, 1)
        except ValueError:
            to_date = today
            from_date = date(today.year, 1, 1)
    else:
        # Original behavior with from_date and to_date
        from_date_str = request.args.get('from_date', f'{today.year}-01-01')
        to_date_str = request.args.get('to_date', str(today))

        try:
            from_date = date.fromisoformat(from_date_str)
        except ValueError:
            from_date = date(today.year, 1, 1)

        try:
            to_date = date.fromisoformat(to_date_str)
        except ValueError:
            to_date = today

    # Get all accounts ordered by account number
    accounts = Account.query.order_by(Account.account_number).all()

    # Organize accounts by class (Revenue, Cost of Sales, Expenses)
    revenue_accounts = []
    cost_of_sales_accounts = []
    expense_accounts = []

    total_revenue = 0
    total_cost_of_sales = 0
    total_expenses = 0

    for account in accounts:
        if not account.account_type:
            continue

        account_class = account.account_type.account_class
        if not account_class:
            continue

        # Calculate balance for the period (to_date) and beginning balance (from_date - 1 day)
        ending_balance = account.balance(to_date)

        # For beginning balance, we need the day before from_date
        beginning_balance = account.balance(from_date - timedelta(days=1)) if from_date else 0

        # Period activity is the difference
        period_balance = ending_balance - beginning_balance

        # Skip accounts with zero activity in the period
        if period_balance == 0:
            continue

        account_data = {
            'number': account.account_number,
            'title': account.account_title,
            'type': account.account_type.account_type_name,
            'balance': abs(period_balance),
            'debit': account.debit_balance(to_date) - account.debit_balance(from_date - timedelta(days=1)) if from_date else account.debit_balance(to_date),
            'credit': account.credit_balance(to_date) - account.credit_balance(from_date - timedelta(days=1)) if from_date else account.credit_balance(to_date),
        }

        class_name = account_class.account_class_name.upper()
        type_name = account.account_type.account_type_name.upper()

        # Income Statement should only include temporary accounts (Revenue, COGS, Expenses)
        # Exclude balance sheet accounts even if their type name contains keywords
        is_balance_sheet_account = (
            'ASSET' in class_name or
            'LIABILIT' in class_name or
            'EQUITY' in class_name or
            'CAPITAL' in class_name
        )

        if is_balance_sheet_account:
            # Skip balance sheet accounts (e.g., PREPAID EXPENSES, DEFERRED TAX ASSETS)
            continue
        elif 'REVENUE' in class_name or 'INCOME' in class_name or 'SALES' in type_name:
            revenue_accounts.append(account_data)
            total_revenue += account_data['credit'] - account_data['debit']
        elif 'COST OF SALES' in type_name or 'COST OF GOODS' in type_name:
            cost_of_sales_accounts.append(account_data)
            total_cost_of_sales += account_data['debit'] - account_data['credit']
        elif 'EXPENSE' in class_name or 'EXPENSE' in type_name:
            expense_accounts.append(account_data)
            total_expenses += account_data['debit'] - account_data['credit']

    # Group revenue by type
    revenue_by_type = {}
    for rev in revenue_accounts:
        type_name = rev['type']
        if type_name not in revenue_by_type:
            revenue_by_type[type_name] = []
        revenue_by_type[type_name].append(rev)

    # Group cost of sales by type
    cost_of_sales_by_type = {}
    for cos in cost_of_sales_accounts:
        type_name = cos['type']
        if type_name not in cost_of_sales_by_type:
            cost_of_sales_by_type[type_name] = []
        cost_of_sales_by_type[type_name].append(cos)

    # Group expenses by type
    expenses_by_type = {}
    for expense in expense_accounts:
        type_name = expense['type']
        if type_name not in expenses_by_type:
            expenses_by_type[type_name] = []
        expenses_by_type[type_name].append(expense)

    # Calculate totals
    gross_profit = total_revenue - total_cost_of_sales
    net_income = gross_profit - total_expenses

    context = {
        "from_date": from_date,
        "to_date": to_date,
        "today": today,
        "revenue_by_type": revenue_by_type,
        "cost_of_sales_by_type": cost_of_sales_by_type,
        "expenses_by_type": expenses_by_type,
        "total_revenue": total_revenue,
        "total_cost_of_sales": total_cost_of_sales,
        "total_expenses": total_expenses,
        "gross_profit": gross_profit,
        "net_income": net_income,
    }

    # Check if AJAX request - return just content without base template
    if request.args.get('ajax') == '1':
        return render_template("income_statement/content.html", **context)

    return render_template("income_statement/home.html", **context)


@bp.route("/download_excel", methods=["GET"])
@login_required
def download_excel():
    """
    Download Income Statement as Excel file
    """
    # Get date parameters
    today = date.today()
    date_param = request.args.get('date')

    if date_param:
        try:
            to_date = datetime.strptime(date_param, '%Y-%m-%d').date()
            from_date = date(to_date.year, 1, 1)
        except ValueError:
            to_date = today
            from_date = date(today.year, 1, 1)
    else:
        from_date = date(today.year, 1, 1)
        to_date = today

    # Get all accounts
    accounts = Account.query.order_by(Account.account_number).all()

    # Prepare data for Excel
    data_rows = []

    # Revenue section
    data_rows.append(['REVENUE', '', ''])
    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue
        class_name = account.account_type.account_class.account_class_name.upper()
        type_name = account.account_type.account_type_name.upper()

        ending_balance = account.balance(to_date)
        beginning_balance = account.balance(from_date - timedelta(days=1))
        period_balance = ending_balance - beginning_balance

        if period_balance == 0:
            continue

        if 'REVENUE' in class_name or 'INCOME' in class_name or 'SALES' in type_name:
            credit = account.credit_balance(to_date) - account.credit_balance(from_date - timedelta(days=1))
            debit = account.debit_balance(to_date) - account.debit_balance(from_date - timedelta(days=1))
            amount = credit - debit
            if amount != 0:
                data_rows.append([
                    f"{account.account_number} - {account.account_title}",
                    account.account_type.account_type_name,
                    amount
                ])

    # Expenses section
    data_rows.append(['', '', ''])
    data_rows.append(['EXPENSES', '', ''])
    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue
        class_name = account.account_type.account_class.account_class_name.upper()
        type_name = account.account_type.account_type_name.upper()

        ending_balance = account.balance(to_date)
        beginning_balance = account.balance(from_date - timedelta(days=1))
        period_balance = ending_balance - beginning_balance

        if period_balance == 0:
            continue

        if 'EXPENSE' in class_name or 'EXPENSE' in type_name or 'COST OF SALES' in type_name:
            debit = account.debit_balance(to_date) - account.debit_balance(from_date - timedelta(days=1))
            credit = account.credit_balance(to_date) - account.credit_balance(from_date - timedelta(days=1))
            amount = debit - credit
            if amount != 0:
                data_rows.append([
                    f"{account.account_number} - {account.account_title}",
                    account.account_type.account_type_name,
                    amount
                ])

    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=['Account', 'Type', 'Amount'])

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Income Statement', index=False)
    output.seek(0)

    # Send file
    filename = f"income_statement_{from_date}_to_{to_date}.xlsx"
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
