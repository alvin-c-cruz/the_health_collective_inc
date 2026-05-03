from flask import Blueprint, render_template, redirect, url_for, flash, send_file, current_app, request, abort
from flask_login import login_required, current_user
from datetime import datetime, timedelta

from application import db
from .extensions import create_ledger, create_ledger_all

from .. account import Account
from .. books_of_accounts.sales import Sales
from .. books_of_accounts_extra.sales_extra import SalesExtra
from .. books_of_accounts.receipt import Receipt
from .. books_of_accounts_extra.receipt_extra import ReceiptExtra
from .. books_of_accounts.accounts_payable import AccountsPayable
from .. books_of_accounts_extra.accounts_payable_extra import AccountsPayableExtra
from .. books_of_accounts.disbursement import Disbursement
from .. books_of_accounts_extra.disbursement_extra import DisbursementExtra
from .. books_of_accounts.general import General
from .. books_of_accounts_extra.general_extra import GeneralExtra


bp = Blueprint("ledger", __name__, template_folder="pages", url_prefix="/ledger")


@bp.route("/", methods=["GET", "POST"])
@login_required
def home():
    transactions = []
    cmd_button = ""
    beginning = 0

    if request.method == "POST":
        account_number = request.form["account_number"]
        date_from = datetime.strptime(request.form["date_from"], "%Y-%m-%d")
        date_to = datetime.strptime(request.form["date_to"], "%Y-%m-%d")
        cmd_button = request.form["cmd_button"]

    else:
        account_number = ""

        today = datetime.today()
        first_day = datetime(today.year, today.month, 1)
        last_day = datetime(today.year, today.month + 1, 1) if today.month != 12 else datetime(today.year + 1, 1, 1)
        last_day -= timedelta(days=1)

        date_from = first_day
        date_to = last_day

    if True:
        module_name = {
            Sales: "sales", 
            SalesExtra: "sales_extra", 
            Receipt: "receipt", 
            ReceiptExtra: "receipts_extra",
            AccountsPayable: "accounts_payable",
            AccountsPayableExtra: "accounts_payable_extra",
            Disbursement: "disbursement",
            DisbursementExtra: "disbursements_extra",
            General: "general",
            GeneralExtra: "general_extra",
        }

        book = {
            Sales: "SJ-Corp", 
            SalesExtra: "SJ-Extra", 
            Receipt: "CR-Corp", 
            ReceiptExtra: "CR-Extra",
            AccountsPayable: "AP-Corp",
            AccountsPayableExtra: "APJ-Extra",
            Disbursement: "CD-Corp",
            DisbursementExtra: "CD-Extra",
            General: "GJ-Corp",
            GeneralExtra: "GJ-Extra"
        }

        # Beginning
        for obj in (
                    Sales, 
                    SalesExtra, 
                    Receipt, 
                    ReceiptExtra,
                    AccountsPayable,
                    AccountsPayableExtra,
                    Disbursement,
                    DisbursementExtra,
                    General,
                    GeneralExtra
                    ):
            vouchers = obj.query.filter(obj.record_date<date_from).all()
            for voucher in vouchers:
                for entry in voucher.entries:
                    if entry.account.account_number == account_number.split(":")[0]:
                        beginning += entry.debit - entry.credit

        # Transactions
        for obj in (
                    Sales, 
                    SalesExtra, 
                    Receipt, 
                    ReceiptExtra,
                    AccountsPayable,
                    AccountsPayableExtra,
                    Disbursement,
                    DisbursementExtra,
                    General,
                    GeneralExtra,
                    ):
            vouchers = obj.query.filter(obj.record_date>=date_from, obj.record_date<=date_to).all()
            for voucher in vouchers:
                for entry in voucher.entries:
                    if entry.account.account_number == account_number.split(":")[0]:
                        transaction = {
                                "record_id": voucher.id,
                                "date": voucher.record_date,
                                "bank_date": voucher.bank_date if hasattr(voucher, "bank_date") else voucher.record_date,
                                "book": book[obj],
                                "reference": getattr(voucher, "record_number"),
                                "particulars": voucher.notes,
                                "debit": entry.debit,
                                "credit": entry.credit,
                                "formatted_debit": '{:,.2f}'.format(entry.debit),
                                "formatted_credit": '{:,.2f}'.format(entry.credit),
                                "date_posted": voucher.date_posted if hasattr(voucher, "date_posted") else "",
                                "edit_url": url_for(module_name[obj] + ".edit", id=voucher.id),
                                "view_url": url_for(module_name[obj] + ".view", id=voucher.id)  if hasattr(voucher, "date_posted") else "",
                            }
                        
                        if obj in (Sales,SalesExtra, Receipt, ReceiptExtra,):
                            description = voucher.customer.customer_name
                        elif obj in (AccountsPayable, AccountsPayableExtra, Disbursement, DisbursementExtra):
                            description = voucher.vendor.vendor_name
                        else:
                            description = ""

                        transaction["description"] = description
                        
                        if obj in (Disbursement, DisbursementsX):
                            check_number = voucher.check_number
                        else:
                            check_number = ""
                            
                        transaction["check_number"] = check_number
                            
                        transactions.append(transaction)


    sorted_transactions = sorted(transactions, key=lambda x: (x['date'], x['book']))

    if cmd_button == "Download":
        account = Accounts.query.filter(Accounts.account_number==account_number.split(":")[0]).first()
        filename = create_ledger(account, beginning, sorted_transactions, date_from, date_to, current_app.instance_path)
        return send_file('{}'.format(filename), as_attachment=True)

    elif cmd_button == "Download All":
        accounts = Accounts.query.all()
        filename = create_ledger_all(accounts, date_from, date_to, current_app.instance_path)
        return send_file('{}'.format(filename), as_attachment=True)

    context = {
        "date_from": str(date_from)[:10],
        "date_to": str(date_to)[:10],
        "account_number": account_number,
        "transactions": sorted_transactions,
        "beginning": beginning,
    }

    return render_template("ledger/home.html", **context)


@bp.route('/<int:account_id>/<year>/<month>')
@login_required
def view(account_id, year, month):
    VALID_MONTHS = {
        'beg': 'Beginning Balance',
        'jan': 'January',
        'feb': 'February',
        'mar': 'March',
        'apr': 'April',
        'may': 'May',
        'jun': 'June',
        'jul': 'July',
        'aug': 'August',
        'sep': 'September',
        'oct': 'October',
        'nov': 'November',
        'dec': 'December',
    }    
    
    if month not in VALID_MONTHS:
        abort(404)

    # Example: fetch account
    account = Accounts.query.get_or_404(account_id)

    # Example: fetch ledger entries
    entries = (
        # LedgerEntry.query
        # .filter_by(account_id=account_id, year, month=month)
        # .order_by(LedgerEntry.date)
        # .all()
    )

    return render_template(
        'ledger/view.html',
        account=account,
        entries=entries,
        year=year,
        month=month,
        month_label=VALID_MONTHS[month],
    )