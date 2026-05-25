from datetime import date
from sqlalchemy import func, select as sa_select

from application.extensions import db
from ..operations.daily_sales.models import (Transaction, TransactionDetail, TransactionTender, TransactionType,
                                              FundReceived, FundDisbursed, Deposit, PettyCashVoucher)
from ..operations.daily_sales.admin_models import AdminTransaction
from ..register.product.models import Product
from ..register.product_type.models import ProductType
from ..register.tender.models import Tender


def get_dashboard_stats(today: date) -> dict:
    today_str = today.strftime("%Y-%m-%d")
    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")
    year_start_str = today.replace(month=1, day=1).strftime("%Y-%m-%d")

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

    # Year-to-date
    ytd_count = (
        db.session.query(func.count(Transaction.id))
        .filter(Transaction.record_date >= year_start_str,
                Transaction.record_date <= today_str, active)
        .scalar() or 0
    )
    ytd_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(Transaction.record_date >= year_start_str,
                Transaction.record_date <= today_str, active)
        .scalar() or 0.0
    )
    ytd_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(Transaction.record_date >= year_start_str,
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
    pending_transactions_count = (
        db.session.query(func.count(Transaction.id))
        .filter(
            Transaction.submitted != None,
            Transaction.submitted != '',
            active,
            Transaction.id.notin_(approved_ids_select)
        )
        .scalar() or 0
    )

    # Pending deposit approvals: deposits with status = 'submitted'
    pending_deposits_count = (
        db.session.query(func.count(Deposit.id))
        .filter(Deposit.status == 'submitted')
        .scalar() or 0
    )

    # Pending petty cash vouchers: PCVs with status = 'submitted'
    pending_pcv_count = (
        db.session.query(func.count(PettyCashVoucher.id))
        .filter(PettyCashVoucher.status == 'submitted')
        .scalar() or 0
    )

    # Total pending approvals (transactions + deposits + petty cash vouchers)
    pending_approval_count = pending_transactions_count + pending_deposits_count + pending_pcv_count

    # Sales Summary by Product Type and Transaction Type (Month-to-Date)
    # Get all active product types
    product_types = ProductType.query.all()

    transaction_types = TransactionType.query.filter_by(active=True).order_by(
        TransactionType.sort_order.desc()
    ).all()

    # Build sales data: sales[product_type_name][transaction_type] = {tender: amount}
    sales_summary = {}
    product_type_totals = {}

    for pt in product_types:
        sales_summary[pt.product_type_name] = {}
        product_type_totals[pt.product_type_name] = 0
        for tt in transaction_types:
            sales_summary[pt.product_type_name][tt.type_code] = {'total': 0, 'tenders': {}}

    # Query MTD transactions
    mtd_transactions = Transaction.query.filter(
        Transaction.record_date >= month_start_str,
        Transaction.record_date <= today_str,
        Transaction.submitted.isnot(None),
        active
    ).all()

    for txn in mtd_transactions:
        txn_type_code = txn.transaction_type.type_code if txn.transaction_type else 'walk_in'

        # Determine product type for this transaction based on transaction details
        # Group products by their product type
        product_type_amounts = {}  # {product_type_name: amount}

        for detail in txn.transaction_details:
            if detail.product and detail.product.product_type:
                pt_name = detail.product.product_type.product_type_name
                if pt_name not in product_type_amounts:
                    product_type_amounts[pt_name] = 0
                product_type_amounts[pt_name] += (detail.amount - detail.discount)

        # If transaction has no product details or product types, skip it
        if not product_type_amounts:
            continue

        # Distribute tender amounts proportionally across product types
        total_txn_amount = sum(product_type_amounts.values())

        for tender_record in txn.transaction_tenders:
            tender_name = tender_record.tender.tender_name if tender_record.tender else 'Unknown'

            for pt_name, pt_amount in product_type_amounts.items():
                # Calculate proportional amount for this product type
                if total_txn_amount > 0:
                    proportion = pt_amount / total_txn_amount
                    allocated_amount = tender_record.amount * proportion
                else:
                    allocated_amount = 0

                if pt_name in sales_summary:
                    if txn_type_code not in sales_summary[pt_name]:
                        sales_summary[pt_name][txn_type_code] = {'total': 0, 'tenders': {}}

                    current = sales_summary[pt_name][txn_type_code]['tenders'].get(tender_name, 0)
                    sales_summary[pt_name][txn_type_code]['tenders'][tender_name] = current + allocated_amount
                    sales_summary[pt_name][txn_type_code]['total'] += allocated_amount
                    product_type_totals[pt_name] += allocated_amount

    # Pending fund cancellations
    pending_fund_cancellations = (
        FundReceived.query.filter_by(status='pending_cancellation').count() +
        FundDisbursed.query.filter_by(status='pending_cancellation').count()
    )

    # Calculate total uncollected tender receivables grouped by tender
    total_uncollected = 0
    uncollected_by_tender = {}
    try:
        from ..operations.collections.models import CollectionDetail

        # Get all receivable tender IDs (tenders that are not cash)
        receivable_tenders = Tender.query.filter(
            ~Tender.tender_name.ilike('%cash%')
        ).all()
        receivable_tender_ids = [t.id for t in receivable_tenders]

        # Get all transaction tenders for receivable types from approved transactions
        if receivable_tender_ids:
            receivable_transaction_tenders = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .filter(
                    TransactionTender.tender_id.in_(receivable_tender_ids),
                    Transaction.submitted.isnot(None),
                    active
                )
                .all()
            )

            # Calculate outstanding for each, grouped by tender
            for tt in receivable_transaction_tenders:
                # Get total collected for this transaction tender
                collected = (
                    db.session.query(func.sum(CollectionDetail.amount_applied))
                    .filter(CollectionDetail.transaction_tender_id == tt.id)
                    .scalar() or 0
                )
                outstanding = tt.amount - collected
                if outstanding > 0:
                    tender_name = tt.tender.tender_name if tt.tender else 'Unknown'
                    uncollected_by_tender[tender_name] = uncollected_by_tender.get(tender_name, 0) + outstanding
                    total_uncollected += outstanding
    except Exception as e:
        # If calculation fails, default to 0
        print(f"Error calculating uncollected receivables: {e}")
        total_uncollected = 0
        uncollected_by_tender = {}

    return {
        "today": today,
        "today_count": today_count,
        "today_net_sales": round(today_sales - today_discounts, 2),
        "mtd_count": mtd_count,
        "mtd_net_sales": round(mtd_sales - mtd_discounts, 2),
        "ytd_count": ytd_count,
        "ytd_net_sales": round(ytd_sales - ytd_discounts, 2),
        "drafts_count": drafts_count,
        "pending_approval_count": pending_approval_count,
        "pending_fund_cancellations": pending_fund_cancellations,
        "total_uncollected_receivables": round(total_uncollected, 2),
        "uncollected_by_tender": {k: round(v, 2) for k, v in uncollected_by_tender.items()},
        "sales_summary": sales_summary,
        "transaction_types": transaction_types,
        "product_types": product_types,
        "product_type_totals": {k: round(v, 2) for k, v in product_type_totals.items()},
        "month_start": today.replace(day=1),
        "year_start": today.replace(month=1, day=1),
    }
