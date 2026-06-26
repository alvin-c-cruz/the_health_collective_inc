from application.extensions import db

from . import app_name
from .admin_models import AdminAccount as ObjAdmin
from .admin_models import UserAccount as ObjUser


class Account(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    account_number = db.Column(db.String(255))
    account_title = db.Column(db.String(255))
    account_description = db.Column(db.String(255))

    account_type_id = db.Column(
        db.Integer, db.ForeignKey("account_type.id"), nullable=True
    )
    account_type = db.relationship(
        "AccountType", backref="account_type_details", lazy=True
    )

    def __str__(self):
        return f"{self.account_number}: {self.account_title}"

    @property
    def preparer(self):
        obj = ObjUser.query.filter(
            getattr(ObjUser, f"{app_name}_id") == self.id
        ).first()
        return obj

    @property
    def approved(self):
        obj = ObjAdmin.query.filter(
            getattr(ObjAdmin, f"{app_name}_id") == self.id
        ).first()
        return obj

    @property
    def account_name(self):
        return f"{self.account_number}: {self.account_title}"

    @staticmethod
    def _entry_models():
        """(detail_model, parent_model) pairs for the 10 books of accounts.

        Imported lazily so loading this module doesn't drag in every book
        model (and so we avoid the pandas import that lives in the trial
        balance helpers). The detail models all expose account_id/debit/credit;
        the parent models all expose record_date.
        """
        from ..books_of_accounts.accounts_payable import (
            AccountsPayable,
            AccountsPayableDetail,
        )
        from ..books_of_accounts.disbursement import Disbursement, DisbursementDetail
        from ..books_of_accounts.general import General, GeneralDetail
        from ..books_of_accounts.receipt import Receipt, ReceiptDetail
        from ..books_of_accounts.sales import Sales, SalesDetail
        from ..books_of_accounts_extra.accounts_payable_extra import (
            AccountsPayableExtra,
            AccountsPayableExtraDetail,
        )
        from ..books_of_accounts_extra.disbursement_extra import (
            DisbursementExtra,
            DisbursementExtraDetail,
        )
        from ..books_of_accounts_extra.general_extra import (
            GeneralExtra,
            GeneralExtraDetail,
        )
        from ..books_of_accounts_extra.receipt_extra import (
            ReceiptExtra,
            ReceiptExtraDetail,
        )
        from ..books_of_accounts_extra.sales_extra import SalesExtra, SalesExtraDetail

        return (
            (SalesDetail, Sales),
            (ReceiptDetail, Receipt),
            (AccountsPayableDetail, AccountsPayable),
            (DisbursementDetail, Disbursement),
            (GeneralDetail, General),
            (SalesExtraDetail, SalesExtra),
            (ReceiptExtraDetail, ReceiptExtra),
            (AccountsPayableExtraDetail, AccountsPayableExtra),
            (DisbursementExtraDetail, DisbursementExtra),
            (GeneralExtraDetail, GeneralExtra),
        )

    def balance(self, as_of_date=None):
        """
        Calculate balance (sum of debit - credit) up to and including the
        specified date. If as_of_date is None, calculate the all-time balance.

        Uses one grouped SQL SUM per book instead of loading every journal
        entry into Python, so cost scales with the number of books (fixed),
        not the number of transactions. Results are memoized per instance
        keyed by as_of_date because report views call balance() /
        debit_balance() / credit_balance() several times per account in a
        single render.
        """
        if not hasattr(self, "_balance_cache"):
            self._balance_cache = {}
        if as_of_date in self._balance_cache:
            return self._balance_cache[as_of_date]

        # record_date is stored as an ISO "YYYY-MM-DD" string, so a lexical
        # comparison matches chronological order. Reduce a date/datetime to its
        # date portion to compare against that format.
        as_of_str = (
            as_of_date.isoformat()[:10]
            if hasattr(as_of_date, "isoformat")
            else as_of_date
        )

        total = 0.0
        for detail_model, parent_model in self._entry_models():
            query = db.session.query(
                db.func.sum(detail_model.debit - detail_model.credit)
            ).filter(detail_model.account_id == self.id)
            if as_of_str is not None:
                query = query.join(parent_model).filter(
                    parent_model.record_date <= as_of_str
                )
            total += query.scalar() or 0.0

        self._balance_cache[as_of_date] = total
        return total

    @classmethod
    def balances_as_of(cls, as_of_date=None):
        """Return {account_id: balance} for every account as of a date.

        Uses one grouped SUM per book (~10 queries total) instead of one query
        per account, so the cost of a whole-chart report does not grow with the
        number of accounts. Accounts with no entries are simply absent from the
        dict (callers should treat a missing key as 0.0).
        """
        as_of_str = (
            as_of_date.isoformat()[:10]
            if hasattr(as_of_date, "isoformat")
            else as_of_date
        )

        totals: dict[int, float] = {}
        for detail_model, parent_model in cls._entry_models():
            query = db.session.query(
                detail_model.account_id,
                db.func.sum(detail_model.debit - detail_model.credit),
            ).group_by(detail_model.account_id)
            if as_of_str is not None:
                query = query.join(parent_model).filter(
                    parent_model.record_date <= as_of_str
                )
            for account_id, amount in query.all():
                totals[account_id] = totals.get(account_id, 0.0) + (amount or 0.0)
        return totals

    @classmethod
    def warm_balance_cache(cls, accounts, *as_of_dates):
        """Pre-populate each account's per-instance balance cache for the given
        dates using bulk queries.

        Report views call balance()/debit_balance()/credit_balance() several
        times per account across a handful of dates. Warming the cache up front
        turns those calls into cache hits, replacing ~(accounts x books)
        per-account queries with ~(dates x books) grouped queries while leaving
        the balance arithmetic untouched.
        """
        for as_of_date in as_of_dates:
            totals = cls.balances_as_of(as_of_date)
            for account in accounts:
                if not hasattr(account, "_balance_cache"):
                    account._balance_cache = {}
                account._balance_cache[as_of_date] = totals.get(account.id, 0.0)

    def formatted_balance(self, as_of_date=None):
        return f"{self.balance(as_of_date):,.2f}"

    def debit_balance(self, as_of_date=None):
        bal = self.balance(as_of_date)
        if bal > 0:
            return bal
        return 0

    def credit_balance(self, as_of_date=None):
        bal = self.balance(as_of_date)
        if bal < 0:
            return -bal
        return 0

    def formatted_debit_balance(self, as_of_date=None):
        return f"{self.debit_balance(as_of_date):,.2f}"

    def formatted_credit_balance(self, as_of_date=None):
        return f"{self.credit_balance(as_of_date):,.2f}"
