from datetime import date
from sqlalchemy import func, select as sa_select

from application.extensions import db
from ..operations.daily_sales.models import Transaction, TransactionDetail, TransactionTender, TransactionType
from ..operations.daily_sales.admin_models import AdminTransaction
from ..register.product.models import Product
from ..register.tender.models import Tender


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

    # Sales Summary by Service Type and Transaction Type (Month-to-Date)
    dialysis_product = Product.query.filter(
        (Product.product_name == 'Dialysis') |
        (Product.product_name == 'HEMO DIALYSIS')
    ).first()

    transaction_types = TransactionType.query.filter_by(active=True).order_by(
        TransactionType.sort_order.desc()
    ).all()

    # Build sales data: sales[service_type][transaction_type] = {tender: amount}
    sales_summary = {'Dialysis': {}, 'Diagnostics': {}}

    for tt in transaction_types:
        sales_summary['Dialysis'][tt.type_code] = {'total': 0, 'tenders': {}}
        sales_summary['Diagnostics'][tt.type_code] = {'total': 0, 'tenders': {}}

    # Query MTD transactions
    mtd_transactions = Transaction.query.filter(
        Transaction.record_date >= month_start_str,
        Transaction.record_date <= today_str,
        Transaction.submitted.isnot(None),
        active
    ).all()

    for txn in mtd_transactions:
        txn_type_code = txn.transaction_type.type_code if txn.transaction_type else 'walk_in'

        is_dialysis = False
        if dialysis_product and txn.transaction_details:
            is_dialysis = any(d.product_id == dialysis_product.id for d in txn.transaction_details)

        service_category = 'Dialysis' if is_dialysis else 'Diagnostics'

        if txn_type_code not in sales_summary[service_category]:
            sales_summary[service_category][txn_type_code] = {'total': 0, 'tenders': {}}

        for tender_record in txn.transaction_tenders:
            tender_name = tender_record.tender.tender_name if tender_record.tender else 'Unknown'
            current = sales_summary[service_category][txn_type_code]['tenders'].get(tender_name, 0)
            sales_summary[service_category][txn_type_code]['tenders'][tender_name] = current + tender_record.amount
            sales_summary[service_category][txn_type_code]['total'] += tender_record.amount

    # Calculate category totals
    diagnostics_total = sum(
        sales_summary['Diagnostics'][tt]['total']
        for tt in sales_summary['Diagnostics']
    )
    dialysis_total = sum(
        sales_summary['Dialysis'][tt]['total']
        for tt in sales_summary['Dialysis']
    )

    return {
        "today": today,
        "today_count": today_count,
        "today_net_sales": round(today_sales - today_discounts, 2),
        "mtd_count": mtd_count,
        "mtd_net_sales": round(mtd_sales - mtd_discounts, 2),
        "drafts_count": drafts_count,
        "pending_approval_count": pending_approval_count,
        "sales_summary": sales_summary,
        "transaction_types": transaction_types,
        "diagnostics_total": round(diagnostics_total, 2),
        "dialysis_total": round(dialysis_total, 2),
        "month_start": today.replace(day=1),
    }
