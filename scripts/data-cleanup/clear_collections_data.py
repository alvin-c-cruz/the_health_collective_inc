"""
Clear all data from collections models
"""
from application import create_app
from application.extensions import db
from application.blueprints.operations.collections.models import Collection, CollectionDetail

# Set up Flask app context
app = create_app()

with app.app_context():
    # Delete in order respecting foreign key constraints

    print("Deleting collection details...")
    count = CollectionDetail.query.delete()
    print(f"  Deleted {count} collection detail records")

    print("Deleting collections...")
    count = Collection.query.delete()
    print(f"  Deleted {count} collection records")

    db.session.commit()

    print("\nAll collections data cleared successfully!")
    print("Database is now clean and ready for fresh data.")
