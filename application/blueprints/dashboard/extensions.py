from datetime import date
from sqlalchemy import func, select as sa_select

from application.extensions import db
from ..operations.daily_sales.models import Transaction, TransactionDetail
from ..operations.daily_sales.admin_models import AdminTransaction


def get_dashboard_stats(today: date) -> dict:
    today_str = today.strftime("%Y-%m-%d")
    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")

    active = (
        (Transaction.cancelled == None) |
        (Transaction.cancelled == '') |
        (Transaction.cancelled == '0') |
        (Transaction.cancelled == False)
    )

    # Today
    today_count = (
        db.session.query(func.count(Transaction.id))
        .filter(Transaction.record_date == today_str, active)
        .scalar() or 0
    )
    today_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(Transaction.record_date == today_str, active)
        .scalar() or 0.0
    )
    today_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(Transaction.record_date == today_str, active)
        .scalar() or 0.0
    )

    # Month-to-date
    mtd_count = (
        db.session.query(func.count(Transaction.id))
        .filter(Transaction.record_date >= month_start_str,
                Transaction.record_date <= today_str, active)
        .scalar() or 0
    )
    mtd_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(Transaction.record_date >= month_start_str,
                Transaction.record_date <= today_str, active)
        .scalar() or 0.0
    )
    mtd_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(Transaction.record_date >= month_start_str,
                Transaction.record_date <= today_str, active)
        .scalar() or 0.0
    )

    # Drafts: not submitted, not cancelled
    drafts_count = (
        db.session.query(func.count(Transaction.id))
        .filter(
            (Transaction.submitted == None) | (Transaction.submitted == ''),
            active
        )
        .scalar() or 0
    )

    # Pending approval: submitted but no AdminTransaction record
    approved_ids_select = sa_select(AdminTransaction.transaction_id)
    pending_approval_count = (
        db.session.query(func.count(Transaction.id))
        .filter(
            Transaction.submitted != None,
            Transaction.submitted != '',
            active,
            Transaction.id.notin_(approved_ids_select)
        )
        .scalar() or 0
    )

    return {
        "today": today,
        "today_count": today_count,
        "today_net_sales": round(today_sales - today_discounts, 2),
        "mtd_count": mtd_count,
        "mtd_net_sales": round(mtd_sales - mtd_discounts, 2),
        "drafts_count": drafts_count,
        "pending_approval_count": pending_approval_count,
    }
