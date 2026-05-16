import pandas as pd
from datetime import datetime
from sqlalchemy import extract
from application import db


def entry_date_info(model):
    if model.__name__ == "SalesDetail":
        from .. books_of_accounts.sales import Sales
        return model, Sales.record_date, Sales

    if model.__name__ == "ReceiptDetail":
        from .. books_of_accounts.receipt import Receipt
        return model, Receipt.record_date, Receipt

    if model.__name__ == "AccountsPayableDetail":
        from .. books_of_accounts.accounts_payable import AccountsPayable
        return model, AccountsPayable.record_date, AccountsPayable

    if model.__name__ == "DisbursementDetail":
        from .. books_of_accounts.disbursement import Disbursement
        return model, Disbursement.record_date, Disbursement

    if model.__name__ == "GeneralDetail":
        from .. books_of_accounts.general import General
        return model, General.record_date, General

    if model.__name__ == "SalesExtraDetail":
        from .. books_of_accounts_extra.sales_extra import SalesExtra
        return model, SalesExtra.record_date, SalesExtra

    if model.__name__ == "ReceiptExtraDetail":
        from .. books_of_accounts_extra.receipt_extra import ReceiptExtra
        return model, ReceiptExtra.record_date, ReceiptExtra

    if model.__name__ == "AccountsPayableExtraDetail":
        from .. books_of_accounts_extra.accounts_payable_extra import AccountsPayableExtra
        return model, AccountsPayableExtra.record_date, AccountsPayableExtra

    if model.__name__ == "DisbursementExtraDetail":
        from .. books_of_accounts_extra.disbursement_extra import DisbursementExtra
        return model, DisbursementExtra.record_date, DisbursementExtra

    if model.__name__ == "GeneralExtraDetail":
        from .. books_of_accounts_extra.general_extra import GeneralExtra
        return model, GeneralExtra.record_date, GeneralExtra

    raise RuntimeError(f"No date mapping for {model.__name__}")


def trial_balance_dataframe(year: int):
    from .. account import Account

    from .. books_of_accounts.sales import SalesDetail
    from .. books_of_accounts.receipt import ReceiptDetail
    from .. books_of_accounts.accounts_payable import AccountsPayableDetail
    from .. books_of_accounts.disbursement import DisbursementDetail
    from .. books_of_accounts.general import GeneralDetail

    from .. books_of_accounts_extra.sales_extra import SalesExtraDetail
    from .. books_of_accounts_extra.receipt_extra import ReceiptExtraDetail
    from .. books_of_accounts_extra.accounts_payable_extra import AccountsPayableExtraDetail
    from .. books_of_accounts_extra.disbursement_extra import DisbursementExtraDetail
    from .. books_of_accounts_extra.general_extra import GeneralExtraDetail

    ENTRY_MODELS = (
        SalesDetail,
        ReceiptDetail,
        AccountsPayableDetail,
        DisbursementDetail,
        GeneralDetail,
        SalesExtraDetail,
        ReceiptExtraDetail,
        AccountsPayableExtraDetail,
        DisbursementExtraDetail,
        GeneralExtraDetail,
    )

    columns = [
        "Beg", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    # -----------------------------
    # INIT DATA (KEY = ACCOUNT ID)
    # -----------------------------
    data = {}

    accounts = Account.query.order_by(Account.account_number).all()

    for acc in accounts:
        data[acc.id] = {
            "Account": f"{acc.account_number}: {acc.account_title}",
            **dict.fromkeys(columns, 0.0),
        }

    # -----------------------------
    # BEGINNING BALANCE
    # -----------------------------
    for model in ENTRY_MODELS:
        m, date_col, parent = entry_date_info(model)

        rows = (
            db.session.query(
                m.account_id,
                db.func.sum(m.debit - m.credit)
            )
            .join(parent)
            .filter(date_col < datetime(year, 1, 1))
            .group_by(m.account_id)
            .all()
        )

        for account_id, amount in rows:
            data[account_id]["Beg"] += amount or 0.0

    # -----------------------------
    # MONTHLY MOVEMENTS
    # -----------------------------
    for model in ENTRY_MODELS:
        m, date_col, parent = entry_date_info(model)

        rows = (
            db.session.query(
                m.account_id,
                extract("month", date_col),
                db.func.sum(m.debit - m.credit)
            )
            .join(parent)
            .filter(extract("year", date_col) == year)
            .group_by(m.account_id, extract("month", date_col))
            .all()
        )

        for account_id, month, amount in rows:
            data[account_id][columns[int(month)]] += amount or 0.0

    # -----------------------------
    # BUILD DATAFRAME
    # -----------------------------
    df = pd.DataFrame.from_dict(data, orient="index")
    df.index.name = "account_id"
    df.reset_index(inplace=True)

    return df
