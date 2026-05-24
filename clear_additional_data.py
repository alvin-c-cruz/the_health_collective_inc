"""
Clear companies, APE batches, and bank account data
"""
from application import create_app
from application.extensions import db
from application.blueprints.register.company.models import Company
from application.blueprints.operations.ape_batch.models import ApeBatch
from application.blueprints.operations.bank_account.models import BankAccount

# Set up Flask app context
app = create_app()

with app.app_context():
    print("Clearing additional data...")
    print()

    # Clear companies
    print("Deleting companies...")
    count = Company.query.delete()
    print(f"  Deleted {count} companies")

    # Clear APE batches
    print("Deleting APE batches...")
    count = ApeBatch.query.delete()
    print(f"  Deleted {count} APE batches")

    # Clear bank accounts
    print("Deleting bank accounts...")
    count = BankAccount.query.delete()
    print(f"  Deleted {count} bank accounts")

    db.session.commit()

    print()
    print("Data cleared successfully!")
