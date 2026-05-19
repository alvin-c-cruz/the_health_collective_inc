from flask import Blueprint, render_template, request
from flask_login import login_required
from datetime import date

from .. account import Account
from .. account_type import AccountType
from .. account_class import AccountClass


bp = Blueprint("balance_sheet", __name__, template_folder="pages", url_prefix="/balance_sheet")


@bp.route("/", methods=["GET"])
@login_required
def home():
    """
    Balance Sheet - Statement of Financial Position
    Shows Assets, Liabilities, and Equity as of a specific date
    """
    # Get date parameter
    today = date.today()
    date_str = request.args.get('as_of_date', str(today))
    try:
        as_of_date = date.fromisoformat(date_str)
    except ValueError:
        as_of_date = today

    # Get all accounts ordered by account number
    accounts = Account.query.order_by(Account.account_number).all()

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
            'number': account.account_number,
            'title': account.account_title,
            'type': account.account_type.account_type_name,
            'balance': abs(balance),
            'debit': account.debit_balance(as_of_date),
            'credit': account.credit_balance(as_of_date),
        }

        class_name = account_class.account_class_name.upper()

        if 'ASSET' in class_name:
            assets.append(account_data)
            total_assets += account.debit_balance(as_of_date) - account.credit_balance(as_of_date)
        elif 'LIABILIT' in class_name:
            liabilities.append(account_data)
            total_liabilities += account.credit_balance(as_of_date) - account.debit_balance(as_of_date)
        elif 'EQUITY' in class_name or 'CAPITAL' in class_name:
            equity.append(account_data)
            total_equity += account.credit_balance(as_of_date) - account.debit_balance(as_of_date)

    # Group assets by type
    assets_by_type = {}
    for asset in assets:
        type_name = asset['type']
        if type_name not in assets_by_type:
            assets_by_type[type_name] = []
        assets_by_type[type_name].append(asset)

    # Group liabilities by type
    liabilities_by_type = {}
    for liability in liabilities:
        type_name = liability['type']
        if type_name not in liabilities_by_type:
            liabilities_by_type[type_name] = []
        liabilities_by_type[type_name].append(liability)

    # Group equity by type
    equity_by_type = {}
    for eq in equity:
        type_name = eq['type']
        if type_name not in equity_by_type:
            equity_by_type[type_name] = []
        equity_by_type[type_name].append(eq)

    context = {
        "as_of_date": as_of_date,
        "today": today,
        "assets_by_type": assets_by_type,
        "liabilities_by_type": liabilities_by_type,
        "equity_by_type": equity_by_type,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "total_liabilities_and_equity": total_liabilities + total_equity,
    }

    return render_template("balance_sheet/home.html", **context)
