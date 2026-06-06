from datetime import date

from sqlalchemy import func
from sqlalchemy import select as sa_select

from application.extensions import db

from ..operations.daily_sales.admin_models import AdminTransaction
from ..operations.daily_sales.models import (
    Deposit,
    FundDisbursed,
    FundReceived,
    PettyCashVoucher,
    Transaction,
    TransactionDetail,
    TransactionTender,
    TransactionType,
)
from ..register.product.models import Product
from ..register.product_type.models import ProductType
from ..register.tender.models import Tender


def get_dashboard_stats(today: date) -> dict:
    from datetime import timedelta

    from dateutil.relativedelta import relativedelta

    today_str = today.strftime("%Y-%m-%d")
    month_start_str = today.replace(day=1).strftime("%Y-%m-%d")
    year_start_str = today.replace(month=1, day=1).strftime("%Y-%m-%d")

    # Calculate comparison dates
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.strftime("%Y-%m-%d")

    last_month = today - relativedelta(months=1)
    last_month_start_str = last_month.replace(day=1).strftime("%Y-%m-%d")
    last_month_end_str = (
        last_month.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    last_year = today - relativedelta(years=1)
    last_year_start_str = last_year.replace(month=1, day=1).strftime("%Y-%m-%d")
    last_year_end_str = last_year.replace(month=12, day=31).strftime("%Y-%m-%d")

    # Only include submitted (not draft) and not cancelled transactions
    active = (
        (Transaction.cancelled == None)
        | (Transaction.cancelled == "")
        | (Transaction.cancelled == "0")
        | (Transaction.cancelled == False)
    )

    submitted = (Transaction.submitted != None) & (Transaction.submitted != "")

    # Today
    today_count = (
        db.session.query(func.count(Transaction.id))
        .filter(Transaction.record_date == today_str, active, submitted)
        .scalar()
        or 0
    )
    today_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(
            Transaction.record_date == today_str,
            active,
            submitted,
            TransactionDetail.billable == True,
        )
        .scalar()
        or 0.0
    )
    today_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(Transaction.record_date == today_str, active, submitted)
        .scalar()
        or 0.0
    )

    # Month-to-date
    mtd_count = (
        db.session.query(func.count(Transaction.id))
        .filter(
            Transaction.record_date >= month_start_str,
            Transaction.record_date <= today_str,
            active,
            submitted,
        )
        .scalar()
        or 0
    )
    mtd_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(
            Transaction.record_date >= month_start_str,
            Transaction.record_date <= today_str,
            active,
            submitted,
            TransactionDetail.billable == True,
        )
        .scalar()
        or 0.0
    )
    mtd_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(
            Transaction.record_date >= month_start_str,
            Transaction.record_date <= today_str,
            active,
            submitted,
        )
        .scalar()
        or 0.0
    )

    # Year-to-date
    ytd_count = (
        db.session.query(func.count(Transaction.id))
        .filter(
            Transaction.record_date >= year_start_str,
            Transaction.record_date <= today_str,
            active,
            submitted,
        )
        .scalar()
        or 0
    )
    ytd_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(
            Transaction.record_date >= year_start_str,
            Transaction.record_date <= today_str,
            active,
            submitted,
            TransactionDetail.billable == True,
        )
        .scalar()
        or 0.0
    )
    ytd_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(
            Transaction.record_date >= year_start_str,
            Transaction.record_date <= today_str,
            active,
            submitted,
        )
        .scalar()
        or 0.0
    )

    # Yesterday (for comparison)
    yesterday_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(
            Transaction.record_date == yesterday_str,
            active,
            submitted,
            TransactionDetail.billable == True,
        )
        .scalar()
        or 0.0
    )
    yesterday_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(Transaction.record_date == yesterday_str, active, submitted)
        .scalar()
        or 0.0
    )

    # Last Month (full month for comparison)
    last_month_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(
            Transaction.record_date >= last_month_start_str,
            Transaction.record_date <= last_month_end_str,
            active,
            submitted,
            TransactionDetail.billable == True,
        )
        .scalar()
        or 0.0
    )
    last_month_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(
            Transaction.record_date >= last_month_start_str,
            Transaction.record_date <= last_month_end_str,
            active,
            submitted,
        )
        .scalar()
        or 0.0
    )

    # Last Year (full year for comparison)
    last_year_sales = (
        db.session.query(func.sum(TransactionDetail.amount))
        .join(Transaction)
        .filter(
            Transaction.record_date >= last_year_start_str,
            Transaction.record_date <= last_year_end_str,
            active,
            submitted,
            TransactionDetail.billable == True,
        )
        .scalar()
        or 0.0
    )
    last_year_discounts = (
        db.session.query(func.sum(Transaction.discount))
        .filter(
            Transaction.record_date >= last_year_start_str,
            Transaction.record_date <= last_year_end_str,
            active,
            submitted,
        )
        .scalar()
        or 0.0
    )

    # Drafts: ALL records with status='draft' across all modules
    # Count draft transactions (legacy: using submitted field)
    draft_transactions_count = (
        db.session.query(func.count(Transaction.id))
        .filter((Transaction.submitted == None) | (Transaction.submitted == ""), active)
        .scalar()
        or 0
    )

    # Count draft deposits
    draft_deposits_count = (
        db.session.query(func.count(Deposit.id))
        .filter(Deposit.status == "draft")
        .scalar()
        or 0
    )

    # Count draft petty cash vouchers
    draft_pcv_count = (
        db.session.query(func.count(PettyCashVoucher.id))
        .filter(PettyCashVoucher.status == "draft")
        .scalar()
        or 0
    )

    # Count draft funds received
    draft_funds_received_count = (
        db.session.query(func.count(FundReceived.id))
        .filter(FundReceived.status == "draft")
        .scalar()
        or 0
    )

    # Count draft funds disbursed
    draft_funds_disbursed_count = (
        db.session.query(func.count(FundDisbursed.id))
        .filter(FundDisbursed.status == "draft")
        .scalar()
        or 0
    )

    # Count draft collections
    try:
        from ..operations.collections.models import Collection

        draft_collections_count = (
            db.session.query(func.count(Collection.id))
            .filter(Collection.status == "draft")
            .scalar()
            or 0
        )
    except:
        draft_collections_count = 0

    # Total drafts across all modules
    drafts_count = (
        draft_transactions_count
        + draft_deposits_count
        + draft_pcv_count
        + draft_funds_received_count
        + draft_funds_disbursed_count
        + draft_collections_count
    )

    # Pending approval: submitted but no AdminTransaction record
    approved_ids_select = sa_select(AdminTransaction.transaction_id)
    pending_transactions_count = (
        db.session.query(func.count(Transaction.id))
        .filter(
            Transaction.submitted != None,
            Transaction.submitted != "",
            active,
            Transaction.id.notin_(approved_ids_select),
        )
        .scalar()
        or 0
    )

    # Pending deposit approvals: deposits with status = 'submitted'
    pending_deposits_count = (
        db.session.query(func.count(Deposit.id))
        .filter(Deposit.status == "submitted")
        .scalar()
        or 0
    )

    # Pending petty cash vouchers: PCVs with status = 'submitted'
    pending_pcv_count = (
        db.session.query(func.count(PettyCashVoucher.id))
        .filter(PettyCashVoucher.status == "submitted")
        .scalar()
        or 0
    )

    # Pending funds received: FRs with status = 'submitted'
    pending_funds_received_count = (
        db.session.query(func.count(FundReceived.id))
        .filter(FundReceived.status == "submitted")
        .scalar()
        or 0
    )

    # Pending funds disbursed: FDs with status = 'submitted'
    pending_funds_disbursed_count = (
        db.session.query(func.count(FundDisbursed.id))
        .filter(FundDisbursed.status == "submitted")
        .scalar()
        or 0
    )

    # Pending collections: collections with status = 'submitted'
    try:
        from ..operations.collections.models import Collection

        pending_collections_count = (
            db.session.query(func.count(Collection.id))
            .filter(Collection.status == "submitted")
            .scalar()
            or 0
        )
    except:
        pending_collections_count = 0

    # Total pending approvals across all modules
    pending_approval_count = (
        pending_transactions_count
        + pending_deposits_count
        + pending_pcv_count
        + pending_funds_received_count
        + pending_funds_disbursed_count
        + pending_collections_count
    )

    # Sales Summary by Product Type and Transaction Type
    # Get all active product types
    product_types = ProductType.query.all()

    transaction_types = (
        TransactionType.query.filter_by(active=True)
        .order_by(TransactionType.sort_order.desc())
        .all()
    )

    # Helper function to calculate demographics for a date range
    def calculate_demographics(start_date_str, end_date_str):
        """Calculate sales summary by product type and transaction type for a date range."""
        sales_summary = {}
        product_type_totals = {}

        for pt in product_types:
            sales_summary[pt.product_type_name] = {}
            product_type_totals[pt.product_type_name] = 0
            for tt in transaction_types:
                sales_summary[pt.product_type_name][tt.type_code] = {
                    "total": 0,
                    "tenders": {},
                }

        # Query transactions for the date range (only submitted, not drafts)
        transactions = Transaction.query.filter(
            Transaction.record_date >= start_date_str,
            Transaction.record_date <= end_date_str,
            submitted,
            active,
        ).all()

        for txn in transactions:
            txn_type_code = (
                txn.transaction_type.type_code if txn.transaction_type else "walk_in"
            )

            # Determine product type for this transaction based on transaction details
            # Group products by their product type
            product_type_amounts = {}  # {product_type_name: amount}

            for detail in txn.transaction_details:
                if detail.billable and detail.product and detail.product.product_type:
                    pt_name = detail.product.product_type.product_type_name
                    if pt_name not in product_type_amounts:
                        product_type_amounts[pt_name] = 0
                    product_type_amounts[pt_name] += detail.amount - detail.discount

            # If transaction has no product details or product types, skip it
            if not product_type_amounts:
                continue

            # Distribute tender amounts proportionally across product types
            total_txn_amount = sum(product_type_amounts.values())

            for tender_record in txn.transaction_tenders:
                tender_name = (
                    tender_record.tender.tender_name
                    if tender_record.tender
                    else "Unknown"
                )

                for pt_name, pt_amount in product_type_amounts.items():
                    # Calculate proportional amount for this product type
                    if total_txn_amount > 0:
                        proportion = pt_amount / total_txn_amount
                        allocated_amount = tender_record.amount * proportion
                    else:
                        allocated_amount = 0

                    if pt_name in sales_summary:
                        if txn_type_code not in sales_summary[pt_name]:
                            sales_summary[pt_name][txn_type_code] = {
                                "total": 0,
                                "tenders": {},
                            }

                        current = sales_summary[pt_name][txn_type_code]["tenders"].get(
                            tender_name, 0
                        )
                        sales_summary[pt_name][txn_type_code]["tenders"][
                            tender_name
                        ] = current + allocated_amount
                        sales_summary[pt_name][txn_type_code]["total"] += (
                            allocated_amount
                        )
                        product_type_totals[pt_name] += allocated_amount

        return sales_summary, product_type_totals

    # Helper function to calculate product-level demographics for Dialysis
    def calculate_dialysis_product_demographics(start_date_str, end_date_str):
        """Calculate sales by individual products under Dialysis product type."""

        dialysis_product_sales = {}

        # Get Dialysis product type
        dialysis_pt = ProductType.query.filter_by(product_type_name="DIALYSIS").first()
        if not dialysis_pt:
            return {}

        # Get all products under Dialysis
        dialysis_products = Product.query.filter_by(
            product_type_id=dialysis_pt.id
        ).all()

        # Initialize sales tracking for each product
        for product in dialysis_products:
            dialysis_product_sales[product.product_name] = 0

        # Query transactions for the date range
        transactions = Transaction.query.filter(
            Transaction.record_date >= start_date_str,
            Transaction.record_date <= end_date_str,
            submitted,
            active,
        ).all()

        # Calculate sales for each Dialysis product
        for txn in transactions:
            for detail in txn.transaction_details:
                if (
                    detail.billable
                    and detail.product
                    and detail.product.product_type_id == dialysis_pt.id
                ):
                    product_name = detail.product.product_name
                    if product_name in dialysis_product_sales:
                        dialysis_product_sales[product_name] += (
                            detail.amount - detail.discount
                        )

        return dialysis_product_sales

    # Calculate demographics for Daily, MTD, and YTD
    daily_sales_summary, daily_product_type_totals = calculate_demographics(
        today_str, today_str
    )
    mtd_sales_summary, mtd_product_type_totals = calculate_demographics(
        month_start_str, today_str
    )
    ytd_sales_summary, ytd_product_type_totals = calculate_demographics(
        year_start_str, today_str
    )

    # Calculate Dialysis product demographics
    daily_dialysis_products = calculate_dialysis_product_demographics(
        today_str, today_str
    )
    mtd_dialysis_products = calculate_dialysis_product_demographics(
        month_start_str, today_str
    )
    ytd_dialysis_products = calculate_dialysis_product_demographics(
        year_start_str, today_str
    )

    # Helper function to calculate receivables report
    def calculate_receivables_report(start_date_str, end_date_str):
        """Calculate receivables: beginning balance, current receivables, collections, ending balance."""
        try:
            from ..operations.collections.models import Collection, CollectionDetail

            # Get receivable tender IDs (tenders marked as receivable)
            receivable_tenders = Tender.query.filter(Tender.is_receivable == True).all()
            receivable_tender_ids = [t.id for t in receivable_tenders]

            if not receivable_tender_ids:
                return {
                    "beginning_balance": 0,
                    "current_receivables": 0,
                    "collections": 0,
                    "ending_balance": 0,
                }

            # Calculate beginning balance (all uncollected receivables before start_date)
            beginning_transactions = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .filter(
                    TransactionTender.tender_id.in_(receivable_tender_ids),
                    Transaction.record_date < start_date_str,
                    submitted,
                    active,
                )
                .all()
            )

            beginning_balance = 0
            for tt in beginning_transactions:
                collected = (
                    db.session.query(func.sum(CollectionDetail.amount_applied))
                    .filter(CollectionDetail.transaction_tender_id == tt.id)
                    .scalar()
                    or 0
                )
                outstanding = tt.amount - collected
                if outstanding > 0:
                    beginning_balance += outstanding

            # Calculate current receivables (new receivables during the period)
            current_transactions = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .filter(
                    TransactionTender.tender_id.in_(receivable_tender_ids),
                    Transaction.record_date >= start_date_str,
                    Transaction.record_date <= end_date_str,
                    submitted,
                    active,
                )
                .all()
            )

            current_receivables = sum(tt.amount for tt in current_transactions)

            # Calculate collections (payments received during the period)
            collections_in_period = (
                db.session.query(func.sum(CollectionDetail.amount_applied))
                .join(Collection)
                .filter(
                    Collection.collection_date >= start_date_str,
                    Collection.collection_date <= end_date_str,
                    Collection.status.in_(["submitted", "posted"]),
                )
                .scalar()
                or 0
            )

            # Calculate ending balance
            ending_balance = (
                beginning_balance + current_receivables - collections_in_period
            )

            return {
                "beginning_balance": round(beginning_balance, 2),
                "current_receivables": round(current_receivables, 2),
                "collections": round(collections_in_period, 2),
                "ending_balance": round(ending_balance, 2),
            }

        except Exception as e:
            print(f"Error calculating receivables: {e}")
            return {
                "beginning_balance": 0,
                "current_receivables": 0,
                "collections": 0,
                "ending_balance": 0,
            }

    # Calculate receivables for Daily, MTD, and YTD
    daily_receivables = calculate_receivables_report(today_str, today_str)
    mtd_receivables = calculate_receivables_report(month_start_str, today_str)
    ytd_receivables = calculate_receivables_report(year_start_str, today_str)

    # Helper function to get detailed receivable transactions
    def get_detailed_receivables():
        """Get list of all outstanding receivable transactions with details."""
        try:
            from ..operations.collections.models import CollectionDetail
            from ..register.customer.models import Customer

            # Get receivable tender IDs
            receivable_tenders = Tender.query.filter(Tender.is_receivable == True).all()
            receivable_tender_ids = [t.id for t in receivable_tenders]

            if not receivable_tender_ids:
                return []

            # Get all receivable transaction tenders with transaction and customer info
            receivable_items = []
            transaction_tenders = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .join(Customer, Transaction.customer_id == Customer.id)
                .join(Tender, TransactionTender.tender_id == Tender.id)
                .filter(
                    TransactionTender.tender_id.in_(receivable_tender_ids),
                    submitted,
                    active,
                )
                .order_by(Transaction.record_date.desc(), Transaction.id.desc())
                .all()
            )

            for tt in transaction_tenders:
                # Calculate collected amount
                collected = (
                    db.session.query(func.sum(CollectionDetail.amount_applied))
                    .filter(CollectionDetail.transaction_tender_id == tt.id)
                    .scalar()
                    or 0
                )
                outstanding = tt.amount - collected

                if outstanding > 0.01:  # Only include if there's outstanding balance
                    receivable_items.append(
                        {
                            "transaction_id": tt.transaction.id,
                            "record_number": tt.transaction.record_number,
                            "record_date": tt.transaction.record_date,
                            "customer_name": tt.transaction.customer.customer_name
                            if tt.transaction.customer
                            else "—",
                            "tender_name": tt.tender.tender_name,
                            "total_amount": round(tt.amount, 2),
                            "collected": round(collected, 2),
                            "outstanding": round(outstanding, 2),
                        }
                    )

            return receivable_items

        except Exception as e:
            print(f"Error getting detailed receivables: {e}")
            return []

    # Helper function to get receivables grouped by tender type
    def get_receivables_by_tender():
        """Get receivables grouped by tender type with transaction details."""
        try:
            from ..operations.collections.models import CollectionDetail
            from ..register.customer.models import Customer

            # Get receivable tender IDs
            receivable_tenders = Tender.query.filter(Tender.is_receivable == True).all()
            receivable_tender_ids = [t.id for t in receivable_tenders]

            if not receivable_tender_ids:
                return []

            # Get all receivable transaction tenders
            transaction_tenders = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .join(Customer, Transaction.customer_id == Customer.id)
                .join(Tender, TransactionTender.tender_id == Tender.id)
                .filter(
                    TransactionTender.tender_id.in_(receivable_tender_ids),
                    submitted,
                    active,
                )
                .order_by(
                    Tender.tender_name,
                    Transaction.record_date.desc(),
                    Transaction.id.desc(),
                )
                .all()
            )

            # Group by tender type
            tender_groups = {}
            for tt in transaction_tenders:
                # Calculate collected amount
                collected = (
                    db.session.query(func.sum(CollectionDetail.amount_applied))
                    .filter(CollectionDetail.transaction_tender_id == tt.id)
                    .scalar()
                    or 0
                )
                outstanding = tt.amount - collected

                if outstanding > 0.01:  # Only include if there's outstanding balance
                    tender_name = tt.tender.tender_name

                    if tender_name not in tender_groups:
                        tender_groups[tender_name] = {
                            "tender_name": tender_name,
                            "total_amount": 0,
                            "collected": 0,
                            "outstanding": 0,
                            "transaction_count": 0,
                            "transactions": [],
                        }

                    # Add to tender group
                    tender_groups[tender_name]["total_amount"] += round(tt.amount, 2)
                    tender_groups[tender_name]["collected"] += round(collected, 2)
                    tender_groups[tender_name]["outstanding"] += round(outstanding, 2)
                    tender_groups[tender_name]["transaction_count"] += 1
                    tender_groups[tender_name]["transactions"].append(
                        {
                            "transaction_id": tt.transaction.id,
                            "record_number": tt.transaction.record_number,
                            "record_date": tt.transaction.record_date,
                            "customer_name": tt.transaction.customer.customer_name
                            if tt.transaction.customer
                            else "—",
                            "total_amount": round(tt.amount, 2),
                            "collected": round(collected, 2),
                            "outstanding": round(outstanding, 2),
                        }
                    )

            # Convert dict to list sorted by tender name
            return sorted(tender_groups.values(), key=lambda x: x["tender_name"])

        except Exception as e:
            print(f"Error getting receivables by tender: {e}")
            return []

    # Get detailed receivables (kept for backward compatibility)
    detailed_receivables = get_detailed_receivables()

    # Get receivables grouped by tender
    receivables_by_tender = get_receivables_by_tender()

    # Helper function to calculate undeposited sales
    def calculate_undeposited_report(start_date_str, end_date_str):
        """Calculate undeposited sales: beginning balance, current undeposited, deposits made, ending balance."""
        try:
            from ..operations.daily_sales.models import DepositItem

            # Get cash tender IDs (tenders NOT marked as receivable)
            cash_tenders = Tender.query.filter(Tender.is_receivable == False).all()
            cash_tender_ids = [t.id for t in cash_tenders]

            if not cash_tender_ids:
                return {
                    "beginning_balance": 0,
                    "current_undeposited": 0,
                    "deposits": 0,
                    "ending_balance": 0,
                }

            # Calculate beginning balance (all undeposited cash before start_date)
            beginning_transactions = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .filter(
                    TransactionTender.tender_id.in_(cash_tender_ids),
                    Transaction.record_date < start_date_str,
                    submitted,
                    active,
                )
                .all()
            )

            beginning_balance = 0
            for tt in beginning_transactions:
                # Get total deposited for this transaction tender
                deposited = (
                    db.session.query(func.sum(DepositItem.amount))
                    .join(Deposit)
                    .filter(
                        DepositItem.transaction_id == tt.transaction_id,
                        Deposit.status.in_(["submitted", "posted"]),
                    )
                    .scalar()
                    or 0
                )
                # Get the cash amount for this transaction
                cash_amount = tt.amount
                undeposited = cash_amount - deposited
                if undeposited > 0:
                    beginning_balance += undeposited

            # Calculate current undeposited (new cash sales during the period)
            current_transactions = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .filter(
                    TransactionTender.tender_id.in_(cash_tender_ids),
                    Transaction.record_date >= start_date_str,
                    Transaction.record_date <= end_date_str,
                    submitted,
                    active,
                )
                .all()
            )

            current_undeposited = sum(tt.amount for tt in current_transactions)

            # Calculate deposits made during the period (only for cash transactions)
            # We need to filter deposit items to only include those from transactions with cash tenders
            deposit_items = (
                db.session.query(DepositItem)
                .join(Deposit)
                .join(Transaction, DepositItem.transaction_id == Transaction.id)
                .join(
                    TransactionTender,
                    TransactionTender.transaction_id == Transaction.id,
                )
                .filter(
                    Deposit.record_date >= start_date_str,
                    Deposit.record_date <= end_date_str,
                    Deposit.status.in_(["submitted", "posted"]),
                    TransactionTender.tender_id.in_(cash_tender_ids),
                )
                .all()
            )
            deposits_in_period = sum(item.amount for item in deposit_items)

            # Calculate ending balance
            ending_balance = (
                beginning_balance + current_undeposited - deposits_in_period
            )

            return {
                "beginning_balance": round(beginning_balance, 2),
                "current_undeposited": round(current_undeposited, 2),
                "deposits": round(deposits_in_period, 2),
                "ending_balance": round(ending_balance, 2),
            }

        except Exception as e:
            print(f"Error calculating undeposited sales: {e}")
            return {
                "beginning_balance": 0,
                "current_undeposited": 0,
                "deposits": 0,
                "ending_balance": 0,
            }

    # Calculate undeposited sales for Daily, MTD, and YTD
    daily_undeposited = calculate_undeposited_report(today_str, today_str)
    mtd_undeposited = calculate_undeposited_report(month_start_str, today_str)
    ytd_undeposited = calculate_undeposited_report(year_start_str, today_str)

    # Pending fund cancellations
    pending_fund_cancellations = (
        FundReceived.query.filter_by(status="pending_cancellation").count()
        + FundDisbursed.query.filter_by(status="pending_cancellation").count()
    )

    # Calculate total uncollected tender receivables grouped by tender
    total_uncollected = 0
    uncollected_by_tender = {}
    try:
        from ..operations.collections.models import CollectionDetail

        # Get all receivable tender IDs (tenders marked as receivable)
        receivable_tenders = Tender.query.filter(Tender.is_receivable == True).all()
        receivable_tender_ids = [t.id for t in receivable_tenders]

        # Get all transaction tenders for receivable types from submitted transactions
        if receivable_tender_ids:
            receivable_transaction_tenders = (
                db.session.query(TransactionTender)
                .join(Transaction)
                .filter(
                    TransactionTender.tender_id.in_(receivable_tender_ids),
                    submitted,
                    active,
                )
                .all()
            )

            # Calculate outstanding for each, grouped by tender
            for tt in receivable_transaction_tenders:
                # Get total collected for this transaction tender
                collected = (
                    db.session.query(func.sum(CollectionDetail.amount_applied))
                    .filter(CollectionDetail.transaction_tender_id == tt.id)
                    .scalar()
                    or 0
                )
                outstanding = tt.amount - collected
                if outstanding > 0:
                    tender_name = tt.tender.tender_name if tt.tender else "Unknown"
                    uncollected_by_tender[tender_name] = (
                        uncollected_by_tender.get(tender_name, 0) + outstanding
                    )
                    total_uncollected += outstanding
    except Exception as e:
        # If calculation fails, default to 0
        print(f"Error calculating uncollected receivables: {e}")
        total_uncollected = 0
        uncollected_by_tender = {}

    # Calculate comparison metrics
    yesterday_net = round(yesterday_sales - yesterday_discounts, 2)
    last_month_net = round(last_month_sales - last_month_discounts, 2)
    last_year_net = round(last_year_sales - last_year_discounts, 2)

    today_net = round(today_sales - today_discounts, 2)
    mtd_net = round(mtd_sales - mtd_discounts, 2)
    ytd_net = round(ytd_sales - ytd_discounts, 2)

    # Calculate percentage changes (avoid division by zero)
    today_vs_yesterday_pct = (
        ((today_net - yesterday_net) / yesterday_net * 100) if yesterday_net > 0 else 0
    )
    mtd_vs_last_month_pct = (
        ((mtd_net - last_month_net) / last_month_net * 100) if last_month_net > 0 else 0
    )
    ytd_vs_last_year_pct = (
        ((ytd_net - last_year_net) / last_year_net * 100) if last_year_net > 0 else 0
    )

    return {
        "today": today,
        "today_count": today_count,
        "today_net_sales": today_net,
        "yesterday_net_sales": yesterday_net,
        "today_vs_yesterday_pct": round(today_vs_yesterday_pct, 1),
        "mtd_count": mtd_count,
        "mtd_net_sales": mtd_net,
        "last_month_net_sales": last_month_net,
        "mtd_vs_last_month_pct": round(mtd_vs_last_month_pct, 1),
        "ytd_count": ytd_count,
        "ytd_net_sales": ytd_net,
        "last_year_net_sales": last_year_net,
        "ytd_vs_last_year_pct": round(ytd_vs_last_year_pct, 1),
        "drafts_count": drafts_count,
        "pending_approval_count": pending_approval_count,
        "pending_fund_cancellations": pending_fund_cancellations,
        "total_uncollected_receivables": round(total_uncollected, 2),
        "uncollected_by_tender": {
            k: round(v, 2) for k, v in uncollected_by_tender.items()
        },
        # Demographics data for all periods
        "daily_sales_summary": daily_sales_summary,
        "daily_product_type_totals": {
            k: round(v, 2) for k, v in daily_product_type_totals.items()
        },
        "mtd_sales_summary": mtd_sales_summary,
        "mtd_product_type_totals": {
            k: round(v, 2) for k, v in mtd_product_type_totals.items()
        },
        "ytd_sales_summary": ytd_sales_summary,
        "ytd_product_type_totals": {
            k: round(v, 2) for k, v in ytd_product_type_totals.items()
        },
        # Dialysis product-level demographics
        "daily_dialysis_products": {
            k: round(v, 2) for k, v in daily_dialysis_products.items()
        },
        "mtd_dialysis_products": {
            k: round(v, 2) for k, v in mtd_dialysis_products.items()
        },
        "ytd_dialysis_products": {
            k: round(v, 2) for k, v in ytd_dialysis_products.items()
        },
        # Receivables report data
        "daily_receivables": daily_receivables,
        "mtd_receivables": mtd_receivables,
        "ytd_receivables": ytd_receivables,
        "detailed_receivables": detailed_receivables,
        "receivables_by_tender": receivables_by_tender,
        # Undeposited sales report data
        "daily_undeposited": daily_undeposited,
        "mtd_undeposited": mtd_undeposited,
        "ytd_undeposited": ytd_undeposited,
        # Keep backwards compatibility with old naming (MTD as default)
        "sales_summary": mtd_sales_summary,
        "product_type_totals": {
            k: round(v, 2) for k, v in mtd_product_type_totals.items()
        },
        "transaction_types": transaction_types,
        "product_types": product_types,
        "month_start": today.replace(day=1),
        "year_start": today.replace(month=1, day=1),
    }


def get_sorted_items(items, section):
    """
    Sort items based on custom sort order from database.
    If no custom order exists, returns items in original order.

    Args:
        items: List of item keys (e.g., tender names)
        section: Section name (e.g., 'payment_methods', 'service_demographics')

    Returns:
        Sorted list of items
    """
    from .sort_order_models import ReportItemSortOrder

    # Get custom sort order from database
    sort_orders = ReportItemSortOrder.query.filter_by(section=section).all()

    if not sort_orders:
        # No custom order, return items as-is
        return items

    # Create mapping of item_key to sort_order
    order_map = {order.item_key: order.sort_order for order in sort_orders}

    # Sort items: custom order first, then unsorted items at end
    sorted_items = sorted(items, key=lambda item: order_map.get(item, 999))

    return sorted_items
