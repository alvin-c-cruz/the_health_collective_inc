"""
Clear patients (customers) and products data
"""
from application import create_app
from application.extensions import db
from application.blueprints.register.customer.models import Customer
from application.blueprints.register.product.models import Product
from application.blueprints.register.product_type.models import ProductType

# Set up Flask app context
app = create_app()

with app.app_context():
    print("Clearing patients and products data...")
    print()

    # Need to delete in order respecting foreign keys
    # First delete user_customer and admin_customer records
    from sqlalchemy import text

    print("Deleting user_customer records...")
    result = db.session.execute(text("DELETE FROM user_customer"))
    count = result.rowcount
    print(f"  Deleted {count} user_customer records")

    print("Deleting admin_customer records...")
    result = db.session.execute(text("DELETE FROM admin_customer"))
    count = result.rowcount
    print(f"  Deleted {count} admin_customer records")

    print("Deleting customers/patients...")
    count = Customer.query.delete()
    print(f"  Deleted {count} customers/patients")

    print("Deleting user_product records...")
    result = db.session.execute(text("DELETE FROM user_product"))
    count = result.rowcount
    print(f"  Deleted {count} user_product records")

    print("Deleting admin_product records...")
    result = db.session.execute(text("DELETE FROM admin_product"))
    count = result.rowcount
    print(f"  Deleted {count} admin_product records")

    print("Deleting products...")
    count = Product.query.delete()
    print(f"  Deleted {count} products")

    print("Deleting user_product_type records...")
    result = db.session.execute(text("DELETE FROM user_product_type"))
    count = result.rowcount
    print(f"  Deleted {count} user_product_type records")

    print("Deleting admin_product_type records...")
    result = db.session.execute(text("DELETE FROM admin_product_type"))
    count = result.rowcount
    print(f"  Deleted {count} admin_product_type records")

    print("Deleting product types...")
    count = ProductType.query.delete()
    print(f"  Deleted {count} product types")

    db.session.commit()

    print()
    print("Patients and products data cleared successfully!")
