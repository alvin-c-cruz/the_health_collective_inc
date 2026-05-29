"""
Assign sequential record numbers to all sales transactions
Format: 00001, 00002, 00003, etc.
"""
from application import create_app, db
from application.blueprints.operations.daily_sales.models import Transaction

app = create_app()

with app.app_context():
    print("="*80)
    print("ASSIGNING RECORD NUMBERS TO TRANSACTIONS")
    print("="*80)
    print()

    # Get all transactions ordered by ID (insertion order)
    all_transactions = Transaction.query.order_by(Transaction.id).all()

    print(f"Total transactions: {len(all_transactions)}")
    print()

    # Check current state
    with_number = sum(1 for t in all_transactions if t.record_number)
    without_number = len(all_transactions) - with_number

    print(f"With record_number: {with_number}")
    print(f"Without record_number: {without_number}")
    print()

    if without_number == 0:
        print("All transactions already have record numbers!")
    else:
        print(f"Assigning record numbers to {without_number} transactions...")
        print()

        # Assign sequential record numbers to ALL transactions
        # This ensures they're in order by ID (time of creation)
        assigned = 0
        updated = 0

        for idx, txn in enumerate(all_transactions, start=1):
            new_record_number = f"{idx:05d}"

            if not txn.record_number:
                txn.record_number = new_record_number
                assigned += 1
                if assigned <= 10:
                    print(f"  Assigned {new_record_number} to Transaction ID {txn.id} ({txn.customer.customer_name})")
            else:
                # Update existing ones to ensure proper sequence
                if txn.record_number != new_record_number:
                    old_number = txn.record_number
                    txn.record_number = new_record_number
                    updated += 1
                    if updated <= 5:
                        print(f"  Updated {old_number} → {new_record_number} for Transaction ID {txn.id}")

        if assigned > 10:
            print(f"  ... and {assigned - 10} more")
        if updated > 5:
            print(f"  ... and {updated - 5} more updated")

        print()
        print(f"Committing changes...")
        db.session.commit()
        print("Done!")

        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"New record numbers assigned: {assigned}")
        print(f"Existing record numbers updated: {updated}")
        print(f"Total transactions: {len(all_transactions)}")
        print()

        # Verify
        print("Verification:")
        first_five = Transaction.query.order_by(Transaction.id).limit(5).all()
        for txn in first_five:
            print(f"  ID {txn.id}: Record# {txn.record_number} - {txn.customer.customer_name}")

        print()
        last_five = Transaction.query.order_by(Transaction.id.desc()).limit(5).all()
        print("Last 5:")
        for txn in reversed(last_five):
            print(f"  ID {txn.id}: Record# {txn.record_number} - {txn.customer.customer_name}")

    print()
    print("="*80)
    print("COMPLETE!")
    print("="*80)
