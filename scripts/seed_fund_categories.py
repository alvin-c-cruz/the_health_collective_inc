"""
Seed script to populate FundCategory table with initial fund categories.
Run this once after creating the fund management models.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import the app
sys.path.insert(0, str(Path(__file__).parent.parent))

from application import create_app, db
from application.blueprints.operations.daily_sales.models import FundCategory

def seed_fund_categories():
    """Create initial fund categories"""
    app = create_app()
    with app.app_context():
        # Check if categories already exist
        existing = FundCategory.query.count()
        if existing > 0:
            print(f"Fund categories already exist ({existing} found). Skipping seed.")
            return

        categories = [
            {
                'category_name': 'Petty Cash',
                'description': 'Small cash fund for minor expenses',
                'sort_order': 1,
                'active': True
            },
            {
                'category_name': 'Change Fund',
                'description': 'Cash fund for making change',
                'sort_order': 2,
                'active': True
            },
        ]

        for cat_data in categories:
            category = FundCategory(**cat_data)
            db.session.add(category)

        db.session.commit()
        print(f"Successfully created {len(categories)} fund categories:")
        for cat in categories:
            print(f"  - {cat['category_name']}")

if __name__ == '__main__':
    seed_fund_categories()
