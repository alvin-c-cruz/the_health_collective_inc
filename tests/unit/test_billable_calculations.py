"""
Unit tests for billable item calculation functions.

Tests all backend functions that calculate transaction amounts to ensure
they correctly filter billable items and exclude non-billable items.

Related to Phase 1 audit bugs #5 and #6.
"""
import pytest
from datetime import date


@pytest.mark.unit
class TestCalculateUndepositedReport:
    """
    Test the calculate_undeposited_report() function in dashboard/extensions.py.

    Bug Fixed: extensions.py:306-311
    - Function was including non-billable items in product type amounts
    - Fixed by adding 'if detail.billable' check
    """

    def test_excludes_non_billable_items_from_product_type_totals(self, app, db):
        """
        Test that non-billable items are excluded from product type amounts.

        This is a regression test for the bug where calculate_undeposited_report()
        was incorrectly including non-billable items in analytics.
        """
        from tests.factories import (
            ProductTypeFactory,
            ProductFactory,
            create_complete_transaction
        )
        from application.blueprints.dashboard.extensions import get_dashboard_stats
        from datetime import date

        with app.app_context():
            # Create product types
            pt_dialysis = ProductTypeFactory(product_type_name='DIALYSIS')
            pt_diagnostic = ProductTypeFactory(product_type_name='DIAGNOSTIC')
            db.flush()

            # Create products
            prod_dialysis = ProductFactory(
                product_name='Hemodialysis Session',
                product_type=pt_dialysis
            )
            prod_medicine = ProductFactory(
                product_name='Medicine',
                product_type=pt_dialysis
            )
            prod_xray = ProductFactory(
                product_name='X-Ray',
                product_type=pt_diagnostic
            )
            db.flush()

            # Create transaction with mix of billable and non-billable items
            today = date.today()
            transaction = create_complete_transaction(
                record_date=str(today),
                status='submitted',
                details=[
                    # Billable dialysis service
                    {'product': prod_dialysis, 'amount': 5000, 'discount': 0, 'billable': True},
                    # Non-billable medicine (dispensed with service, not charged)
                    {'product': prod_medicine, 'amount': 1500, 'discount': 0, 'billable': False},
                    # Billable diagnostic
                    {'product': prod_xray, 'amount': 2000, 'discount': 0, 'billable': True},
                ],
                tenders=[
                    {'tender__tender_name': 'Cash', 'amount': 7000}  # Only billable total
                ]
            )
            db.flush()

            # Act: Get dashboard stats which calls calculate_undeposited_report()
            stats = get_dashboard_stats(today)

            # Assert: Undeposited report should only include billable items
            undeposited = stats.get('undeposited_sales_summary', {})

            # DIALYSIS total should be 5000 (not 6500 with non-billable medicine)
            dialysis_total = 0
            for txn_type, data in undeposited.get('DIALYSIS', {}).items():
                if isinstance(data, dict) and 'total' in data:
                    dialysis_total += data['total']

            assert dialysis_total == 5000, \
                f"DIALYSIS total should be 5000 (billable only), got {dialysis_total}"

            # DIAGNOSTIC total should be 2000
            diagnostic_total = 0
            for txn_type, data in undeposited.get('DIAGNOSTIC', {}).items():
                if isinstance(data, dict) and 'total' in data:
                    diagnostic_total += data['total']

            assert diagnostic_total == 2000, \
                f"DIAGNOSTIC total should be 2000, got {diagnostic_total}"

    def test_all_billable_items_included(self, app, db):
        """Test that all billable items ARE included in calculations."""
        from tests.factories import (
            ProductTypeFactory,
            ProductFactory,
            create_complete_transaction
        )
        from application.blueprints.dashboard.extensions import get_dashboard_stats
        from datetime import date

        with app.app_context():
            # Create product type
            pt_dialysis = ProductTypeFactory(product_type_name='DIALYSIS')
            db.flush()

            # Create products
            prod1 = ProductFactory(product_name='Service 1', product_type=pt_dialysis)
            prod2 = ProductFactory(product_name='Service 2', product_type=pt_dialysis)
            db.flush()

            # Create transaction with all billable items
            today = date.today()
            transaction = create_complete_transaction(
                record_date=str(today),
                status='submitted',
                details=[
                    {'product': prod1, 'amount': 3000, 'discount': 0, 'billable': True},
                    {'product': prod2, 'amount': 2500, 'discount': 500, 'billable': True},
                ]
            )
            db.flush()

            # Act
            stats = get_dashboard_stats(today)
            undeposited = stats.get('undeposited_sales_summary', {})

            # Assert: Total should be 3000 + (2500 - 500) = 5000
            dialysis_total = 0
            for txn_type, data in undeposited.get('DIALYSIS', {}).items():
                if isinstance(data, dict) and 'total' in data:
                    dialysis_total += data['total']

            assert dialysis_total == 5000, \
                f"Expected 5000 (all billable items), got {dialysis_total}"

    def test_all_non_billable_items_excluded(self, app, db):
        """Test that transaction with only non-billable items shows zero."""
        from tests.factories import (
            ProductTypeFactory,
            ProductFactory,
            create_complete_transaction
        )
        from application.blueprints.dashboard.extensions import get_dashboard_stats
        from datetime import date

        with app.app_context():
            # Create product type
            pt_pharmacy = ProductTypeFactory(product_type_name='PHARMACY')
            db.flush()

            # Create products
            prod_medicine = ProductFactory(product_name='Medicine', product_type=pt_pharmacy)
            db.flush()

            # Create transaction with only non-billable items
            today = date.today()
            transaction = create_complete_transaction(
                record_date=str(today),
                status='submitted',
                details=[
                    {'product': prod_medicine, 'amount': 1000, 'discount': 0, 'billable': False},
                ],
                tenders=[
                    {'tender__tender_name': 'Cash', 'amount': 0}  # No billable amount
                ]
            )
            db.flush()

            # Act
            stats = get_dashboard_stats(today)
            undeposited = stats.get('undeposited_sales_summary', {})

            # Assert: PHARMACY should not appear in undeposited (or should be 0)
            pharmacy_total = 0
            for txn_type, data in undeposited.get('PHARMACY', {}).items():
                if isinstance(data, dict) and 'total' in data:
                    pharmacy_total += data['total']

            assert pharmacy_total == 0, \
                f"Expected 0 for non-billable only transaction, got {pharmacy_total}"


@pytest.mark.unit
class TestCalculateDialysisProductDemographics:
    """
    Test the calculate_dialysis_product_demographics() function.

    Bug Fixed: extensions.py:371-375
    - Function was including non-billable dialysis items
    - Fixed by adding 'if detail.billable' check
    """

    def test_excludes_non_billable_dialysis_products(self, app, db):
        """Test that non-billable dialysis products are excluded from demographics."""
        from tests.factories import (
            ProductTypeFactory,
            ProductFactory,
            create_complete_transaction
        )
        from application.blueprints.dashboard.extensions import get_dashboard_stats
        from datetime import date

        with app.app_context():
            # Create DIALYSIS product type
            pt_dialysis = ProductTypeFactory(product_type_name='DIALYSIS')
            db.flush()

            # Create dialysis products
            prod_session = ProductFactory(
                product_name='Hemodialysis Session',
                product_type=pt_dialysis
            )
            prod_medicine = ProductFactory(
                product_name='Dialysis Medicine',
                product_type=pt_dialysis
            )
            db.flush()

            # Create transaction with billable and non-billable dialysis items
            today = date.today()
            transaction = create_complete_transaction(
                record_date=str(today),
                status='submitted',
                details=[
                    # Billable dialysis session
                    {'product': prod_session, 'amount': 5000, 'discount': 0, 'billable': True},
                    # Non-billable dialysis medicine
                    {'product': prod_medicine, 'amount': 2000, 'discount': 0, 'billable': False},
                ]
            )
            db.flush()

            # Act: Get dashboard stats which includes dialysis demographics
            stats = get_dashboard_stats(today)
            daily_dialysis = stats.get('daily_dialysis_products', {})

            # Assert: Session should be 5000, Medicine should be 0
            assert daily_dialysis.get('Hemodialysis Session', 0) == 5000, \
                "Billable dialysis session should be included"
            assert daily_dialysis.get('Dialysis Medicine', 0) == 0, \
                "Non-billable dialysis medicine should be excluded"

    def test_includes_all_billable_dialysis_products(self, app, db):
        """Test that all billable dialysis products are included."""
        from tests.factories import (
            ProductTypeFactory,
            ProductFactory,
            create_complete_transaction
        )
        from application.blueprints.dashboard.extensions import get_dashboard_stats
        from datetime import date

        with app.app_context():
            # Create DIALYSIS product type
            pt_dialysis = ProductTypeFactory(product_type_name='DIALYSIS')
            db.flush()

            # Create multiple billable dialysis products
            prod1 = ProductFactory(product_name='HD Session', product_type=pt_dialysis)
            prod2 = ProductFactory(product_name='PD Session', product_type=pt_dialysis)
            db.flush()

            # Create transactions
            today = date.today()
            txn1 = create_complete_transaction(
                record_date=str(today),
                status='submitted',
                details=[
                    {'product': prod1, 'amount': 5000, 'discount': 0, 'billable': True},
                ]
            )
            txn2 = create_complete_transaction(
                record_date=str(today),
                status='submitted',
                details=[
                    {'product': prod2, 'amount': 4500, 'discount': 500, 'billable': True},
                ]
            )
            db.flush()

            # Act
            stats = get_dashboard_stats(today)
            daily_dialysis = stats.get('daily_dialysis_products', {})

            # Assert
            assert daily_dialysis.get('HD Session', 0) == 5000
            assert daily_dialysis.get('PD Session', 0) == 4000  # 4500 - 500 discount
