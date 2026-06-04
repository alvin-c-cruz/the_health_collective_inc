"""
Bulk Create APE Transactions for COEX Batch
Creates individual APE transactions for all employees in a batch.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask_app import app
from application.extensions import db
from application.blueprints.operations.daily_sales.models import Transaction, TransactionDetail, TransactionTender
from application.blueprints.operations.ape_batch.models import ApeBatch
from application.blueprints.register.customer.models import Customer
from application.blueprints.register.product.models import Product
from application.blueprints.register.tender.models import Tender
from application.blueprints.operations.transaction_type.models import TransactionType
from application.blueprints.register.sex.models import Sex
from datetime import datetime

# Employee list from COEX batch
EMPLOYEES = [
    "ILAGAN JULIO M",
    "MALLARI LALEINNE D",
    "QUITO DAREEN L",
    "ZAMORA JOEL P",
    "FUNDALES ELISA D",
    "SIBUG JANSCEN LHAYNE",
    "ROSAL JEFFERY",
    "CORONEL NESTOR JR",
    "ARCA KARINA MARA C",
    "TAMIDLESMILES RUBY V",
    "GALICHA KEEVIN J",
    "MANLAOP JENNY",
    "ARCENA FRANCISCO JR D",
    "MENESES IAN JAY P",
    "RIVERA DANEL T",
    "OMPAD JAY ANGELO N",
    "BULANADI MARRISA S",
    "BONDOC RAMIL C",
    "CASA ARYLMIN P",
    "CORONEL MELVIN S",
    "DOMINGO JEFFREY F",
    "EVANGELISTA FLORADEL B",
    "MANLUPIG MARLYN C",
    "LUNA ANTONINO D",
    "PAJIMNA MICHAEL B",
    "SALVANA MARCO O",
    "URBINA ROSAL R",
    "PALOMA POLO RALPH C",
    "SENOBIO RAYMUND B",
    "NARVASA JOYSEBLE B",
    "BRONDO LILIBETH M",
    "MANGEL RACHEL G",
    "MANLUPIG CATHERINE C",
    "TANGUILAN CHRISTIAN V",
    "BADOSO MANAGO H",
    "MORALDE ABRAHAM R C",
    "MADRELINO MARCELINO V",
    "RIVERA JERICK A",
    "REYES RICHARD Y",
    "DIOQUINO RAUL A",
]

# Configuration
BATCH_ID = 1  # COEX batch
TRANSACTION_DATE = "2026-03-03"
PACKAGE_AMOUNT = 2147.50
APE_SERVICE_NAME = "Various APE Services"
DEFAULT_SEX = "Female"  # Default if not specified


def parse_name(full_name):
    """Parse full name into last, first, middle"""
    parts = full_name.strip().split()
    if len(parts) == 0:
        return None, None, None
    elif len(parts) == 1:
        return parts[0], None, None
    elif len(parts) == 2:
        return parts[0], parts[1], None
    else:
        # Last name is first word, first name is second, rest is middle
        return parts[0], parts[1], ' '.join(parts[2:])


def create_ape_transaction(employee_name, batch_id, transaction_date, amount, current_user_id,
                          transaction_type_id, ape_product_id, credit_tender_id, default_sex_id):
    """Create a single APE transaction for an employee"""

    # Parse employee name
    last_name, first_name, middle_name = parse_name(employee_name)

    if not last_name:
        print(f"[X] Skipping invalid name: {employee_name}")
        return None

    # Check if customer already exists
    customer = Customer.query.filter_by(
        last_name=last_name,
        first_name=first_name,
        middle_name=middle_name
    ).first()

    if not customer:
        # Create new customer
        customer = Customer(
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            sex_id=default_sex_id
        )
        db.session.add(customer)
        db.session.flush()  # Get customer ID
        print(f"   [+] Created new customer: {employee_name}")
    else:
        print(f"   [+] Found existing customer: {employee_name}")

    # Create transaction
    transaction = Transaction(
        record_date=transaction_date,
        customer_id=customer.id,
        transaction_type_id=transaction_type_id,
        ape_batch_id=batch_id,
        discount=0,
        status='draft',
        created_by_id=current_user_id
    )
    db.session.add(transaction)
    db.session.flush()  # Get transaction ID

    # Create transaction detail (service)
    detail = TransactionDetail(
        transaction_id=transaction.id,
        product_id=ape_product_id,
        amount=amount,
        discount=0
    )
    db.session.add(detail)

    # Create transaction tender (payment)
    tender = TransactionTender(
        transaction_id=transaction.id,
        tender_id=credit_tender_id,
        amount=amount,
        side_note=None
    )
    db.session.add(tender)

    return transaction


def main():
    """Main script execution"""
    with app.app_context():
        print("=" * 60)
        print("BULK APE TRANSACTION CREATION SCRIPT")
        print("=" * 60)

        # Get required data
        print("\n[*] Loading configuration...")

        batch = ApeBatch.query.get(BATCH_ID)
        if not batch:
            print(f"[X] ERROR: APE Batch ID {BATCH_ID} not found!")
            return

        print(f"   [+] Batch: {batch.company.company_name} - {batch.batch_date}")
        print(f"   [+] Package Amount: P{PACKAGE_AMOUNT:,.2f}")

        # Get transaction type
        ape_type = TransactionType.query.filter_by(type_code='ape').first()
        if not ape_type:
            print("[X] ERROR: APE transaction type not found!")
            return
        print(f"   [+] Transaction Type: {ape_type.type_name} (ID: {ape_type.id})")

        # Get or create APE service product
        ape_product = Product.query.filter(Product.product_name.like('%APE%')).first()
        if not ape_product:
            # Create generic APE service
            ape_product = Product(product_name=APE_SERVICE_NAME)
            db.session.add(ape_product)
            db.session.flush()
            print(f"   [+] Created product: {APE_SERVICE_NAME} (ID: {ape_product.id})")
        else:
            print(f"   [+] Product: {ape_product.product_name} (ID: {ape_product.id})")

        # Get credit tender (exact match to avoid getting "Credit Card")
        credit_tender = Tender.query.filter_by(tender_name='Credit').first()
        if not credit_tender:
            print("[X] ERROR: Credit tender not found!")
            return
        print(f"   [+] Tender: {credit_tender.tender_name} (ID: {credit_tender.id})")

        # Get default sex
        default_sex = Sex.query.filter(Sex.sex_name.like(f'%{DEFAULT_SEX}%')).first()
        if not default_sex:
            default_sex = Sex.query.first()
        print(f"   [+] Default Sex: {default_sex.sex_name} (ID: {default_sex.id})")

        # Get current user (assuming user ID 1 is admin/system)
        current_user_id = 1
        print(f"   [+] Created By User ID: {current_user_id}")

        print(f"\n[*] Processing {len(EMPLOYEES)} employees...")
        print("-" * 60)

        created_count = 0
        skipped_count = 0

        for i, employee_name in enumerate(EMPLOYEES, 1):
            print(f"\n[{i}/{len(EMPLOYEES)}] {employee_name}")

            try:
                transaction = create_ape_transaction(
                    employee_name=employee_name,
                    batch_id=BATCH_ID,
                    transaction_date=TRANSACTION_DATE,
                    amount=PACKAGE_AMOUNT,
                    current_user_id=current_user_id,
                    transaction_type_id=ape_type.id,
                    ape_product_id=ape_product.id,
                    credit_tender_id=credit_tender.id,
                    default_sex_id=default_sex.id
                )

                if transaction:
                    created_count += 1
                    print(f"   [OK] Transaction created (ID: {transaction.id})")
                else:
                    skipped_count += 1

            except Exception as e:
                print(f"   [X] ERROR: {str(e)}")
                skipped_count += 1
                db.session.rollback()
                continue

        # Commit all transactions
        print("\n" + "=" * 60)
        print("[*] Saving to database...")
        db.session.commit()
        print("[OK] All transactions saved successfully!")

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total employees:      {len(EMPLOYEES)}")
        print(f"Transactions created: {created_count}")
        print(f"Skipped:             {skipped_count}")
        print(f"Total amount:        P{created_count * PACKAGE_AMOUNT:,.2f}")
        print("=" * 60)
        print("\n[OK] Script completed successfully!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[X] Script interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[X] FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
