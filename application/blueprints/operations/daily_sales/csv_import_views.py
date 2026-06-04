"""
CSV Import Views for Daily Sales Transactions
Handles uploading, reviewing, and importing transactions from CSV files.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import csv
import os
from datetime import datetime

from application.extensions import db
from application.blueprints.user import login_required, roles_accepted
from .models import Transaction, TransactionDetail, TransactionTender
from application.blueprints.register.customer.models import Customer
from application.blueprints.register.product.models import Product
from application.blueprints.register.tender.models import Tender
from application.blueprints.register.sex.models import Sex
from application.blueprints.operations.transaction_type.models import TransactionType
from application.blueprints.audit.utils import log_audit

csv_import_bp = Blueprint('csv_import', __name__, url_prefix='/daily_sales/csv_import')

# Mapping of CSV Referrer values to transaction type codes
# Uses "starts with" matching to handle variants like "WALK IN-CASH", "DIALYSIS PHIC", etc.
REFERRER_TYPE_MAPPING = {
    'WALK IN': 'walk_in',
    'HOME SERVICE': 'home_service',
    'APE': 'ape',
    'DIALYSIS': 'dialysis',
    'HD': 'dialysis',  # HD (Hemodialysis) is also dialysis
    'TELE CONSULT': 'tele_consult',
}

def match_referrer_to_type(referrer):
    """
    Match referrer string to transaction type using 'starts with' logic.
    This handles variants like "WALK IN-CASH", "DIALYSIS PHIC", "HD PHIC", etc.

    Args:
        referrer (str): Referrer string from CSV

    Returns:
        str: Transaction type code, or None if no match
    """
    if not referrer:
        return None

    referrer_upper = referrer.upper().strip()

    # Try exact match first
    if referrer_upper in REFERRER_TYPE_MAPPING:
        return REFERRER_TYPE_MAPPING[referrer_upper]

    # Try "starts with" match for variants
    for key, value in REFERRER_TYPE_MAPPING.items():
        if referrer_upper.startswith(key):
            return value

    return None


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'csv'


def parse_csv_file(filepath):
    """Parse CSV file and return list of transaction rows"""
    transactions = []

    with open(filepath, 'r', encoding='utf-8-sig') as f:
        # Auto-detect delimiter
        sample = f.read(1024)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
            reader = csv.DictReader(f, dialect=dialect)
        except:
            reader = csv.DictReader(f)

        for row in reader:
            # Skip empty rows or summary rows
            if not row.get('Date') or 'TOTAL' in str(row.get('Date', '')).upper():
                continue

            # Clean up column names (remove leading/trailing spaces)
            # Skip None keys to avoid serialization errors
            cleaned_row = {k.strip(): v for k, v in row.items() if k}
            transactions.append(cleaned_row)

    return transactions


def parse_patient_name(full_name):
    """Parse patient name into last, first, middle"""
    if not full_name:
        return None, None, None

    parts = full_name.strip().split()

    if len(parts) == 0:
        return None, None, None
    elif len(parts) == 1:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], parts[1], None
    else:
        return parts[0], parts[1], ' '.join(parts[2:])


def parse_pipe_separated(value):
    """Parse pipe-separated values into list"""
    if not value:
        return []
    return [item.strip() for item in str(value).split('|')]


@csv_import_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@roles_accepted(['Daily Sales'])
def upload():
    """Step 1: Upload CSV file"""
    from flask import abort
    from flask_login import current_user

    # Only superusers can import CSV
    if not current_user.is_superuser:
        abort(403)

    if request.method == 'POST':
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(request.url)

        file = request.files['csv_file']

        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not allowed_file(file.filename):
            flash('Only CSV files are allowed', 'error')
            return redirect(request.url)

        # Get default sex selection
        default_sex_id = request.form.get('default_sex_id', 2)  # Default to Female

        try:
            default_sex_id = int(default_sex_id)
        except (ValueError, TypeError):
            default_sex_id = 2

        # Save file
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(current_app.instance_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Parse CSV
        try:
            transactions = parse_csv_file(filepath)

            if not transactions:
                flash('No valid transactions found in CSV file', 'error')
                os.remove(filepath)
                return redirect(request.url)

            # Check for unknown referrers
            unknown_referrers = set()
            for txn in transactions:
                referrer = (txn.get(' Referrer') or txn.get('Referrer') or '').strip()
                if referrer:
                    # Use the new matching function
                    if match_referrer_to_type(referrer) is None:
                        unknown_referrers.add(referrer)

            # Store file path and settings in session
            session['csv_import_file'] = filepath
            session['csv_import_default_sex'] = default_sex_id
            session['csv_import_transactions'] = transactions
            session['csv_import_unknown_referrers'] = list(unknown_referrers)

            flash(f'CSV file uploaded successfully. Found {len(transactions)} transactions.', 'success')

            # Warn about unknown referrers
            if unknown_referrers:
                referrer_list = ', '.join(f'"{r}"' for r in unknown_referrers)
                flash(f'Warning: Unknown referrers found: {referrer_list}. These transactions will not have a transaction type assigned.', 'warning')

            return redirect(url_for('csv_import.review'))

        except Exception as e:
            flash(f'Error parsing CSV file: {str(e)}', 'error')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(request.url)

    # GET request - show upload form
    sexes = Sex.query.all()

    context = {
        'sexes': sexes,
        'default_sex_id': 2  # Default to Female
    }

    return render_template('daily_sales/csv_import/upload.html', **context)


@csv_import_bp.route('/review', methods=['GET', 'POST'])
@login_required
@roles_accepted(['Daily Sales'])
def review():
    """Step 2: Review and select transactions to import"""
    from flask import abort
    from flask_login import current_user

    # Only superusers can import CSV
    if not current_user.is_superuser:
        abort(403)

    transactions = session.get('csv_import_transactions')

    if not transactions:
        flash('No CSV data found. Please upload a file first.', 'error')
        return redirect(url_for('csv_import.upload'))

    if request.method == 'POST':
        # Get selected transaction indices
        selected_indices = request.form.getlist('selected_transactions')
        selected_indices = [int(i) for i in selected_indices]

        if not selected_indices:
            flash('No transactions selected for import', 'warning')
            return redirect(request.url)

        # Get user-provided referrer mappings
        unknown_referrers = session.get('csv_import_unknown_referrers', [])
        user_mappings = {}
        for ref in unknown_referrers:
            mapping_key = f'referrer_mapping_{ref}'
            if mapping_key in request.form:
                mapping_value = request.form[mapping_key]
                if mapping_value and mapping_value != 'none':
                    user_mappings[ref.upper()] = mapping_value

        # Store selected indices and mappings in session
        session['csv_import_selected'] = selected_indices
        session['csv_import_user_mappings'] = user_mappings

        # Call the import process directly
        return process_import_internal()

    # GET request - show review page
    # Add index to each transaction for selection
    indexed_transactions = []
    for i, txn in enumerate(transactions):
        txn_copy = txn.copy()
        txn_copy['index'] = i

        # Parse products to count items
        products = parse_pipe_separated(txn.get('Product') or txn.get(' Product'))
        txn_copy['product_count'] = len(products)

        indexed_transactions.append(txn_copy)

    # Get unknown referrers from session
    unknown_referrers = session.get('csv_import_unknown_referrers', [])

    # Get all active transaction types from database
    transaction_types = TransactionType.query.filter_by(active=True).order_by(TransactionType.sort_order).all()

    context = {
        'transactions': indexed_transactions,
        'total_count': len(indexed_transactions),
        'unknown_referrers': unknown_referrers,
        'transaction_types': transaction_types
    }

    return render_template('daily_sales/csv_import/review.html', **context)


def process_import_internal():
    """Internal function to process and import selected transactions"""

    transactions = session.get('csv_import_transactions')
    selected_indices = session.get('csv_import_selected')
    default_sex_id = session.get('csv_import_default_sex', 2)
    user_mappings = session.get('csv_import_user_mappings', {})

    if not transactions or not selected_indices:
        flash('No transactions selected for import', 'error')
        return redirect(url_for('csv_import.upload'))

    # Statistics
    stats = {
        'imported': 0,
        'skipped': 0,
        'new_customers': 0,
        'new_products': 0,
        'errors': []
    }

    # Cache for lookups
    customer_cache = {}
    product_cache = {}
    tender_cache = {}

    # Load existing tenders
    for tender in Tender.query.all():
        tender_cache[tender.tender_name.strip().upper()] = tender

    # Helper function to generate record number
    def generate_record_number():
        last = Transaction.query.filter(
            Transaction.record_number.isnot(None)
        ).order_by(Transaction.record_number.desc()).first()
        if last and last.record_number:
            try:
                seq = int(last.record_number) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{seq:05d}"

    # Sort selected transactions by dashlabs_number (receipt number)
    selected_transactions = []
    for index in selected_indices:
        if index < len(transactions):
            row = transactions[index]
            receipt_num = (row.get(' Receipt Number') or row.get('Receipt Number') or '').strip()
            selected_transactions.append((receipt_num, index, row))

    # Sort by receipt number
    selected_transactions.sort(key=lambda x: x[0])

    try:
        for receipt_num, index, row in selected_transactions:
            try:
                # Parse transaction data
                date_str = (row.get('Date') or '').strip()
                patient_name = (row.get(' Patient') or row.get('Patient') or '').strip()
                status = (row.get(' Status') or row.get('Status') or '').strip()
                tags = (row.get(' Tags') or row.get('Tags') or '').strip()
                referrer = (row.get(' Referrer') or row.get('Referrer') or '').strip()
                mop = (row.get(' MOP') or row.get('MOP') or '').strip()
                products_str = (row.get(' Product') or row.get('Product') or '').strip()
                prices_str = (row.get(' Item Price') or row.get('Item Price') or '').strip()
                discount_str = (row.get(' Discounts') or row.get('Discounts') or '').strip()

                # Convert date format YYYY/MM/DD or MM/DD/YYYY to YYYY-MM-DD
                if '/' in date_str:
                    parts = date_str.split('/')
                    if len(parts[0]) == 4:  # YYYY/MM/DD
                        record_date = '-'.join(parts)
                    else:  # MM/DD/YYYY
                        record_date = f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
                else:
                    record_date = date_str

                # Find or create customer
                last_name, first_name, middle_name = parse_patient_name(patient_name)

                if not last_name:
                    stats['errors'].append(f"Receipt {receipt_num}: Invalid patient name")
                    stats['skipped'] += 1
                    continue

                customer_key = f"{last_name}|{first_name}".upper()

                if customer_key in customer_cache:
                    customer = customer_cache[customer_key]
                else:
                    customer = Customer.query.filter_by(
                        last_name=last_name,
                        first_name=first_name
                    ).first()

                    if not customer:
                        customer = Customer(
                            last_name=last_name,
                            first_name=first_name,
                            middle_name=middle_name,
                            sex_id=default_sex_id
                        )
                        db.session.add(customer)
                        db.session.flush()  # Get customer.id
                        stats['new_customers'] += 1

                    customer_cache[customer_key] = customer

                # Determine transaction type from referrer
                # Use user-provided mappings first, then fall back to hardcoded mappings
                transaction_type_id = None
                if referrer:
                    referrer_upper = referrer.strip().upper()

                    # Check user-provided mappings first (exact match)
                    type_code = user_mappings.get(referrer_upper)

                    # Fall back to hardcoded mappings if not found (uses starts-with matching)
                    if not type_code:
                        type_code = match_referrer_to_type(referrer)

                    if type_code:
                        txn_type = TransactionType.query.filter_by(type_code=type_code).first()
                        if txn_type:
                            transaction_type_id = txn_type.id

                # Create transaction
                description_parts = []
                if tags:
                    description_parts.append(f"Tags: {tags}")
                if referrer:
                    description_parts.append(f"Referrer: {referrer}")

                # Generate record number
                record_number = generate_record_number()

                transaction = Transaction(
                    record_date=record_date,
                    record_number=record_number,
                    dashlabs_number=receipt_num,
                    customer_id=customer.id,
                    transaction_type_id=transaction_type_id,
                    status='draft',
                    description=' | '.join(description_parts) if description_parts else None,
                    created_by_id=session.get('user_id')
                )

                db.session.add(transaction)
                db.session.flush()  # Get transaction.id

                # Parse products and prices
                products = parse_pipe_separated(products_str)
                prices = parse_pipe_separated(prices_str)

                # Separate positive (regular items) and negative (discounts) prices
                transaction_discount = 0.0

                # Create transaction details only for positive-priced items
                for i, product_name in enumerate(products):
                    if not product_name:
                        continue

                    product_name = product_name.strip()

                    # Get price for this product
                    amount = 0.0
                    if i < len(prices):
                        try:
                            amount = float(prices[i].replace(',', ''))
                        except (ValueError, AttributeError):
                            amount = 0.0

                    # Special handling: Override amount for Dialysis + Philhealth
                    if transaction_type_id and mop:
                        txn_type = TransactionType.query.get(transaction_type_id)
                        if txn_type and txn_type.type_code == 'dialysis':
                            # Check if tender is Philhealth
                            mop_key = mop.strip().upper()
                            tender = tender_cache.get(mop_key)
                            if tender and tender.tender_name and 'philhealth' in tender.tender_name.lower():
                                amount = 6350.00

                    # If negative price, add to transaction discount and skip creating detail
                    if amount < 0:
                        transaction_discount += abs(amount)
                        continue

                    # Only create TransactionDetail for positive prices
                    # Find or create product
                    product_key = product_name.upper()

                    if product_key in product_cache:
                        product = product_cache[product_key]
                    else:
                        product = Product.query.filter_by(product_name=product_name).first()

                        if not product:
                            # Determine product type based on transaction type
                            # DIALYSIS transaction type → DIALYSIS product type (ID 2)
                            # All other transaction types → DIAGNOSTIC product type (ID 1)
                            product_type_id = 1  # Default to DIAGNOSTIC
                            if transaction_type_id:
                                txn_type = TransactionType.query.get(transaction_type_id)
                                if txn_type and txn_type.type_code == 'dialysis':
                                    product_type_id = 2  # DIALYSIS product type

                            product = Product(
                                product_name=product_name,
                                product_type_id=product_type_id
                            )
                            db.session.add(product)
                            db.session.flush()
                            stats['new_products'] += 1

                        product_cache[product_key] = product

                    # Create transaction detail with positive amount
                    detail = TransactionDetail(
                        transaction_id=transaction.id,
                        product_id=product.id,
                        amount=amount
                    )
                    db.session.add(detail)

                # Update transaction with total discount
                if transaction_discount > 0:
                    transaction.discount = transaction_discount

                # Create transaction tender (payment method)
                if mop:
                    mop_key = mop.strip().upper()
                    tender = tender_cache.get(mop_key)

                    if tender:
                        # Use Order Total from CSV (net amount after discounts)
                        order_total_str = (row.get(' Order Total') or row.get('Order Total') or '0').strip()
                        try:
                            total_amount = float(order_total_str.replace(',', ''))
                        except (ValueError, AttributeError):
                            total_amount = 0.0

                        # Special handling: Dialysis + Philhealth = fixed amount of 6,350.00
                        if transaction_type_id:
                            txn_type = TransactionType.query.get(transaction_type_id)
                            if txn_type and txn_type.type_code == 'dialysis':
                                # Check if tender is Philhealth
                                if tender.tender_name and 'philhealth' in tender.tender_name.lower():
                                    total_amount = 6350.00

                        tender_record = TransactionTender(
                            transaction_id=transaction.id,
                            tender_id=tender.id,
                            amount=total_amount
                        )
                        db.session.add(tender_record)

                stats['imported'] += 1

            except Exception as e:
                stats['errors'].append(f"Receipt {receipt_num}: {str(e)}")
                stats['skipped'] += 1
                continue

        # Commit all changes
        db.session.commit()

        # Log CSV import to audit trail
        csv_filename = session.get('csv_import_file', '').split('\\')[-1].split('/')[-1]  # Extract filename from path
        import_summary = {
            'filename': csv_filename,
            'total_imported': stats['imported'],
            'new_customers': stats['new_customers'],
            'new_products': stats['new_products'],
            'skipped': stats['skipped']
        }

        log_audit(
            module='daily_sales',
            action='csv_import',
            record_identifier=f"{csv_filename} — {stats['imported']} transactions",
            new_values=import_summary,
            notes=f"Imported {stats['imported']} transactions from CSV file. New customers: {stats['new_customers']}, New products: {stats['new_products']}, Skipped: {stats['skipped']}"
        )

        # Clean up session
        session.pop('csv_import_file', None)
        session.pop('csv_import_transactions', None)
        session.pop('csv_import_selected', None)
        session.pop('csv_import_default_sex', None)

        # Show results
        flash(f'Import completed! Imported {stats["imported"]} transactions.', 'success')
        if stats['new_customers'] > 0:
            flash(f'Created {stats["new_customers"]} new customers.', 'info')
        if stats['new_products'] > 0:
            flash(f'Created {stats["new_products"]} new products.', 'info')
        if stats['skipped'] > 0:
            flash(f'Skipped {stats["skipped"]} transactions due to errors.', 'warning')

        return redirect(url_for('daily_sales.home'))

    except Exception as e:
        db.session.rollback()
        flash(f'Import failed: {str(e)}', 'error')
        return redirect(url_for('csv_import.review'))


@csv_import_bp.route('/cancel')
@login_required
def cancel():
    """Cancel import and clean up"""
    from flask import abort
    from flask_login import current_user

    # Only superusers can import CSV
    if not current_user.is_superuser:
        abort(403)

    # Clean up uploaded file
    filepath = session.get('csv_import_file')
    if filepath and os.path.exists(filepath):
        try:
            os.remove(filepath)
        except:
            pass

    # Clean up session
    session.pop('csv_import_file', None)
    session.pop('csv_import_transactions', None)
    session.pop('csv_import_selected', None)
    session.pop('csv_import_default_sex', None)

    flash('Import cancelled', 'info')
    return redirect(url_for('daily_sales.home'))
