"""
Test data factories for The Health Collective Inc.

Uses factory_boy to create test data easily and consistently.
"""

import factory
from factory.alchemy import SQLAlchemyModelFactory

# Global session - will be set by conftest.py
_session = None


def bind_factories(session):
    """Bind all factories to the given SQLAlchemy session."""
    global _session
    _session = session


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""

    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "flush"

    @classmethod
    def _get_model_class(cls):
        """Get the actual model class from string if needed."""
        if isinstance(cls._meta.model, str):
            # Import the model class from the string path
            module_path, class_name = cls._meta.model.rsplit(".", 1)
            import importlib

            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        return cls._meta.model

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override to use our global session."""
        # If model_class is still a string, resolve it
        if isinstance(model_class, str):
            model_class = cls._get_model_class()

        obj = model_class(*args, **kwargs)
        _session.add(obj)
        _session.flush()
        return obj


# ============================================================================
# User & Auth Models
# ============================================================================


class UserFactory(BaseFactory):
    """Factory for User model."""

    class Meta:
        model = "application.blueprints.user.models.User"

    user_name = factory.Sequence(lambda n: f"testuser{n}")
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    active = True
    staff = False
    admin = False
    superuser = False

    @factory.post_generation
    def set_password(obj, create, extracted, **kwargs):
        """Set password after creation."""
        if create:
            obj.set_pass_word(extracted or "testpass123")


# ============================================================================
# Register Models (Master Data)
# ============================================================================


class SexFactory(BaseFactory):
    """Factory for Sex model."""

    class Meta:
        model = "application.blueprints.register.sex.models.Sex"

    sex_name = factory.Iterator(["Male", "Female", "Other"])


class ProductTypeFactory(BaseFactory):
    """Factory for ProductType model."""

    class Meta:
        model = "application.blueprints.register.product_type.models.ProductType"

    product_type_name = factory.Iterator(
        ["Dialysis", "Diagnostic", "Laboratory", "Pharmacy", "Consultation"]
    )


class ProductFactory(BaseFactory):
    """Factory for Product model."""

    class Meta:
        model = "application.blueprints.register.product.models.Product"

    product_name = factory.Sequence(lambda n: f"Product {n}")
    product_type = factory.SubFactory(ProductTypeFactory)


class CustomerFactory(BaseFactory):
    """Factory for Customer model."""

    class Meta:
        model = "application.blueprints.register.customer.models.Customer"

    customer_name = factory.Faker("name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    sex = factory.SubFactory(SexFactory)


class TenderFactory(BaseFactory):
    """Factory for Tender model."""

    class Meta:
        model = "application.blueprints.register.tender.models.Tender"

    tender_name = factory.Iterator(["Cash", "GCASH", "Bank Transfer", "Check"])
    is_receivable = False


# ============================================================================
# Operations Models
# ============================================================================


class TransactionTypeFactory(BaseFactory):
    """Factory for TransactionType model."""

    class Meta:
        model = (
            "application.blueprints.operations.transaction_type.models.TransactionType"
        )

    type_code = factory.Sequence(lambda n: f"TT{n:03d}")
    type_name = factory.Iterator(["Walk-in", "Home Service", "Emergency"])
    icon = "bi-tag"
    icon_color = "ic-blue"
    badge_color = "thc-badge-blue"
    active = True
    sort_order = 99


class TransactionFactory(BaseFactory):
    """Factory for Transaction model."""

    class Meta:
        model = "application.blueprints.operations.daily_sales.models.Transaction"

    record_date = "2026-04-08"
    customer = factory.SubFactory(CustomerFactory)
    transaction_type = factory.SubFactory(TransactionTypeFactory)
    discount = 0
    status = "submitted"
    # The real submit/cancel workflow (forms.py / views.py) sets the LEGACY
    # string fields alongside `status`, and dashboard/reporting queries filter
    # on those legacy fields. Mirror that here so factory-built transactions
    # behave like real ones (otherwise they're invisible to the dashboard).
    submitted = factory.LazyAttribute(
        lambda o: (
            o.record_date if o.status in ("submitted", "posted", "cancelled") else None
        )
    )
    cancelled = factory.LazyAttribute(
        lambda o: o.record_date if o.status == "cancelled" else None
    )
    created_by_id = factory.LazyAttribute(lambda obj: UserFactory().id)
    submitted_by_id = factory.SelfAttribute("created_by_id")


class TransactionDetailFactory(BaseFactory):
    """Factory for TransactionDetail model."""

    class Meta:
        model = "application.blueprints.operations.daily_sales.models.TransactionDetail"

    transaction = factory.SubFactory(TransactionFactory)
    product = factory.SubFactory(ProductFactory)
    amount = factory.Faker(
        "pydecimal",
        left_digits=4,
        right_digits=2,
        positive=True,
        min_value=100,
        max_value=10000,
    )
    discount = 0
    billable = True


class TransactionTenderFactory(BaseFactory):
    """Factory for TransactionTender model."""

    class Meta:
        model = "application.blueprints.operations.daily_sales.models.TransactionTender"

    transaction = factory.SubFactory(TransactionFactory)
    tender = factory.SubFactory(TenderFactory)
    amount = factory.Faker(
        "pydecimal",
        left_digits=4,
        right_digits=2,
        positive=True,
        min_value=100,
        max_value=10000,
    )


# ============================================================================
# Helper Functions
# ============================================================================


def create_complete_transaction(**kwargs):
    """
    Helper function to create a complete transaction with details and tenders.

    Usage:
        transaction = create_complete_transaction(
            record_date='2026-04-08',
            status='submitted',
            details=[
                {'product': prod1, 'amount': 5000, 'billable': True},
                {'product': prod2, 'amount': 1500, 'billable': True},
            ]
        )
    """
    details_data = kwargs.pop("details", [])
    tenders_data = kwargs.pop("tenders", None)

    # Create transaction
    transaction = TransactionFactory(**kwargs)

    # Add details
    for detail_data in details_data:
        TransactionDetailFactory(transaction=transaction, **detail_data)

    # Add tenders (default to Cash for total if not provided)
    if tenders_data:
        for tender_data in tenders_data:
            TransactionTenderFactory(transaction=transaction, **tender_data)
    else:
        # Calculate total from billable details
        total = sum(
            d.amount - d.discount for d in transaction.transaction_details if d.billable
        )
        if total > 0:
            TransactionTenderFactory(
                transaction=transaction, tender__tender_name="Cash", amount=total
            )

    return transaction
