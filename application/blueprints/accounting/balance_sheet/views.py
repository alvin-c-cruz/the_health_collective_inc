import io
from datetime import date, datetime, timedelta

import pandas as pd
from flask import Blueprint, render_template, request, send_file
from flask_login import login_required

from ..account import Account

bp = Blueprint(
    "balance_sheet", __name__, template_folder="pages", url_prefix="/balance_sheet"
)


def calculate_retained_earnings(as_of_date):
    """
    Calculate retained earnings breakdown:
    - Beginning retained earnings (all prior years)
    - Net income/loss for current year
    - Ending retained earnings
    """
    # Get beginning of current year
    year_start = date(as_of_date.year, 1, 1)
    prior_year_end = year_start - timedelta(days=1)

    # Get all accounts
    accounts = Account.query.all()

    # One set of bulk queries warms every account's balance for both dates,
    # so the per-account balance() calls below are cache hits.
    Account.warm_balance_cache(accounts, prior_year_end, as_of_date)

    # Calculate revenue and expenses for current year
    revenue_current_year = 0
    expenses_current_year = 0
    beginning_retained_earnings = 0

    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue

        class_name = account.account_type.account_class.account_class_name.upper()
        type_name = account.account_type.account_type_name.upper()

        # Skip balance sheet accounts (Assets, Liabilities, Equity)
        is_balance_sheet_account = (
            "ASSET" in class_name
            or "LIABILIT" in class_name
            or "EQUITY" in class_name
            or "CAPITAL" in class_name
        )

        if is_balance_sheet_account:
            continue

        # Calculate balances
        balance_prior_year = account.balance(prior_year_end)
        balance_as_of_date = account.balance(as_of_date)
        current_year_activity = balance_as_of_date - balance_prior_year

        # Revenue accounts (credit balance = positive revenue)
        if "REVENUE" in class_name or "INCOME" in class_name or "SALES" in type_name:
            revenue_current_year += account.credit_balance(
                as_of_date
            ) - account.debit_balance(as_of_date)
            revenue_current_year -= account.credit_balance(
                prior_year_end
            ) - account.debit_balance(prior_year_end)

        # Expense accounts (debit balance = positive expense)
        elif (
            "EXPENSE" in class_name
            or "EXPENSE" in type_name
            or "COST OF SALES" in type_name
        ):
            expenses_current_year += account.debit_balance(
                as_of_date
            ) - account.credit_balance(as_of_date)
            expenses_current_year -= account.debit_balance(
                prior_year_end
            ) - account.credit_balance(prior_year_end)

    # Net income for current year
    net_income_current_year = revenue_current_year - expenses_current_year

    # Calculate beginning retained earnings from prior period income/expenses
    revenue_prior = 0
    expenses_prior = 0

    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue

        class_name = account.account_type.account_class.account_class_name.upper()
        type_name = account.account_type.account_type_name.upper()

        # Skip balance sheet accounts (Assets, Liabilities, Equity)
        is_balance_sheet_account = (
            "ASSET" in class_name
            or "LIABILIT" in class_name
            or "EQUITY" in class_name
            or "CAPITAL" in class_name
        )

        if is_balance_sheet_account:
            continue

        # Prior year balances
        if "REVENUE" in class_name or "INCOME" in class_name or "SALES" in type_name:
            revenue_prior += account.credit_balance(
                prior_year_end
            ) - account.debit_balance(prior_year_end)

        elif (
            "EXPENSE" in class_name
            or "EXPENSE" in type_name
            or "COST OF SALES" in type_name
        ):
            expenses_prior += account.debit_balance(
                prior_year_end
            ) - account.credit_balance(prior_year_end)

    beginning_retained_earnings = revenue_prior - expenses_prior

    # Ending retained earnings
    ending_retained_earnings = beginning_retained_earnings + net_income_current_year

    return {
        "beginning": beginning_retained_earnings,
        "net_income": net_income_current_year,
        "ending": ending_retained_earnings,
        "year": as_of_date.year,
    }


@bp.route("/", methods=["GET"])
@login_required
def home():
    """
    Balance Sheet - Statement of Financial Position
    Shows Assets, Liabilities, and Equity as of a specific date
    """
    # Get date parameter (support both 'date' and 'as_of_date')
    today = date.today()
    date_str = request.args.get("date") or request.args.get("as_of_date", str(today))
    try:
        if isinstance(date_str, str):
            as_of_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            as_of_date = date_str
    except ValueError:
        as_of_date = today

    # Get all accounts ordered by account number
    accounts = Account.query.order_by(Account.account_number).all()

    # Bulk-load every account's balance as of the report date (one set of
    # grouped queries) so the per-account balance() calls below are cache hits.
    Account.warm_balance_cache(accounts, as_of_date)

    # Organize accounts by class (Assets, Liabilities, Equity)
    assets = []
    liabilities = []
    equity = []

    total_assets = 0
    total_liabilities = 0
    total_equity = 0

    for account in accounts:
        if not account.account_type:
            continue

        account_class = account.account_type.account_class
        if not account_class:
            continue

        balance = account.balance(as_of_date)

        # Skip accounts with zero balance
        if balance == 0:
            continue

        account_data = {
            "number": account.account_number,
            "title": account.account_title,
            "type": account.account_type.account_type_name,
            "balance": abs(balance),
            "debit": account.debit_balance(as_of_date),
            "credit": account.credit_balance(as_of_date),
        }

        class_name = account_class.account_class_name.upper()

        if "ASSET" in class_name:
            assets.append(account_data)
            total_assets += account.debit_balance(as_of_date) - account.credit_balance(
                as_of_date
            )
        elif "LIABILIT" in class_name:
            liabilities.append(account_data)
            total_liabilities += account.credit_balance(
                as_of_date
            ) - account.debit_balance(as_of_date)
        elif "EQUITY" in class_name or "CAPITAL" in class_name:
            equity.append(account_data)
            total_equity += account.credit_balance(as_of_date) - account.debit_balance(
                as_of_date
            )

    # Group assets by type
    assets_by_type = {}
    for asset in assets:
        type_name = asset["type"]
        if type_name not in assets_by_type:
            assets_by_type[type_name] = []
        assets_by_type[type_name].append(asset)

    # Group liabilities by type
    liabilities_by_type = {}
    for liability in liabilities:
        type_name = liability["type"]
        if type_name not in liabilities_by_type:
            liabilities_by_type[type_name] = []
        liabilities_by_type[type_name].append(liability)

    # Group equity by type
    equity_by_type = {}
    for eq in equity:
        type_name = eq["type"]
        if type_name not in equity_by_type:
            equity_by_type[type_name] = []
        equity_by_type[type_name].append(eq)

    # Calculate retained earnings
    retained_earnings = calculate_retained_earnings(as_of_date)

    # Add retained earnings to total equity
    total_equity_with_retained = total_equity + retained_earnings["ending"]

    context = {
        "as_of_date": as_of_date,
        "today": today,
        "assets_by_type": assets_by_type,
        "liabilities_by_type": liabilities_by_type,
        "equity_by_type": equity_by_type,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "retained_earnings": retained_earnings,
        "total_equity_with_retained": total_equity_with_retained,
        "total_liabilities_and_equity": total_liabilities + total_equity_with_retained,
    }

    # Check if AJAX request - return just content without base template
    if request.args.get("ajax") == "1":
        return render_template("balance_sheet/content.html", **context)

    return render_template("balance_sheet/home.html", **context)


@bp.route("/download_excel", methods=["GET"])
@login_required
def download_excel():
    """
    Download Balance Sheet as Excel file
    """
    # Get date parameter
    today = date.today()
    date_str = request.args.get("date", str(today))
    try:
        as_of_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        as_of_date = today

    # Get all accounts
    accounts = Account.query.order_by(Account.account_number).all()

    # Bulk-load balances as of the report date so the per-account calls below
    # are cache hits.
    Account.warm_balance_cache(accounts, as_of_date)

    # Prepare data for Excel
    data_rows = []

    # Assets section
    data_rows.append(["ASSETS", "", ""])
    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue
        class_name = account.account_type.account_class.account_class_name.upper()
        if "ASSET" in class_name:
            balance = account.debit_balance(as_of_date) - account.credit_balance(
                as_of_date
            )
            if balance != 0:
                data_rows.append(
                    [
                        f"{account.account_number} - {account.account_title}",
                        account.account_type.account_type_name,
                        abs(balance),
                    ]
                )

    # Liabilities section
    data_rows.append(["", "", ""])
    data_rows.append(["LIABILITIES", "", ""])
    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue
        class_name = account.account_type.account_class.account_class_name.upper()
        if "LIABILIT" in class_name:
            balance = account.credit_balance(as_of_date) - account.debit_balance(
                as_of_date
            )
            if balance != 0:
                data_rows.append(
                    [
                        f"{account.account_number} - {account.account_title}",
                        account.account_type.account_type_name,
                        abs(balance),
                    ]
                )

    # Equity section
    data_rows.append(["", "", ""])
    data_rows.append(["EQUITY", "", ""])
    for account in accounts:
        if not account.account_type or not account.account_type.account_class:
            continue
        class_name = account.account_type.account_class.account_class_name.upper()
        if "EQUITY" in class_name or "CAPITAL" in class_name:
            balance = account.credit_balance(as_of_date) - account.debit_balance(
                as_of_date
            )
            if balance != 0:
                data_rows.append(
                    [
                        f"{account.account_number} - {account.account_title}",
                        account.account_type.account_type_name,
                        abs(balance),
                    ]
                )

    # Create DataFrame
    df = pd.DataFrame(data_rows, columns=["Account", "Type", "Amount"])

    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Balance Sheet", index=False)
    output.seek(0)

    # Send file
    filename = f"balance_sheet_{date_str}.xlsx"
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )
