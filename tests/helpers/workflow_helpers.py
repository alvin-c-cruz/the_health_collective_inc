"""Workflow testing helpers.

Provides utilities for common workflows like submitting, approving, and canceling
transactions, deposits, and other business objects.
"""

from typing import Any, Dict, Optional


def submit_transaction(
    transaction: "Transaction", user_id: Optional[int] = None
) -> "Transaction":
    """Submit a transaction (move from draft to submitted state).

    Args:
        transaction: Transaction instance to submit
        user_id: ID of user submitting (defaults to created_by_id)

    Returns:
        Updated transaction instance

    Example:
        >>> txn = TransactionFactory(status="draft")
        >>> txn = submit_transaction(txn)
        >>> assert txn.status == "submitted"
        >>> assert txn.submitted is not None
    """
    from datetime import datetime

    from application.extensions import db

    if user_id is None:
        user_id = transaction.created_by_id

    transaction.status = "submitted"
    transaction.submitted = datetime.utcnow()
    transaction.submitted_by_id = user_id

    db.session.add(transaction)
    db.session.commit()
    db.session.refresh(transaction)

    return transaction


def approve_transaction(transaction: "Transaction", approver_id: int) -> "Transaction":
    """Approve a submitted transaction.

    Args:
        transaction: Transaction instance to approve
        approver_id: ID of user approving

    Returns:
        Updated transaction instance

    Example:
        >>> txn = create_and_submit_transaction()
        >>> admin = create_admin_user()
        >>> txn = approve_transaction(txn, admin.id)
        >>> assert txn.approved_by_id == admin.id
    """
    from datetime import datetime

    from application.extensions import db

    if transaction.status != "submitted":
        raise ValueError("Can only approve submitted transactions")

    transaction.approved_by_id = approver_id
    transaction.approved_at = datetime.utcnow()

    db.session.add(transaction)
    db.session.commit()
    db.session.refresh(transaction)

    return transaction


def cancel_transaction(
    transaction: "Transaction", reason: str, user_id: int
) -> "Transaction":
    """Cancel a transaction.

    Args:
        transaction: Transaction instance to cancel
        reason: Reason for cancellation
        user_id: ID of user cancelling

    Returns:
        Updated transaction instance

    Example:
        >>> txn = TransactionFactory(status="submitted")
        >>> txn = cancel_transaction(txn, "Duplicate entry", user.id)
        >>> assert txn.status == "cancelled"
        >>> assert txn.cancelled is not None
    """
    from datetime import datetime

    from application.extensions import db

    transaction.status = "cancelled"
    transaction.cancelled = datetime.utcnow()
    transaction.cancellation_reason = reason
    transaction.cancelled_by_id = user_id

    db.session.add(transaction)
    db.session.commit()
    db.session.refresh(transaction)

    return transaction


def create_and_submit_transaction(**kwargs) -> "Transaction":
    """Create a transaction and immediately submit it.

    Convenience function for tests that need submitted transactions.

    Args:
        **kwargs: Keyword arguments to pass to TransactionFactory

    Returns:
        Created and submitted transaction

    Example:
        >>> txn = create_and_submit_transaction(
        ...     record_date="2026-04-08",
        ...     details=[{"product": prod, "amount": 5000}]
        ... )
        >>> assert txn.status == "submitted"
    """
    from tests.factories import create_complete_transaction

    # Default status to submitted
    kwargs.setdefault("status", "submitted")

    return create_complete_transaction(**kwargs)


def submit_deposit(deposit: "Deposit", user_id: Optional[int] = None) -> "Deposit":
    """Submit a deposit.

    Args:
        deposit: Deposit instance to submit
        user_id: ID of user submitting

    Returns:
        Updated deposit instance

    Example:
        >>> deposit = DepositFactory(status="draft")
        >>> deposit = submit_deposit(deposit)
        >>> assert deposit.status == "submitted"
    """
    from datetime import datetime

    from application.extensions import db

    if user_id is None and hasattr(deposit, "created_by_id"):
        user_id = deposit.created_by_id

    deposit.status = "submitted"
    deposit.submitted = datetime.utcnow()
    if user_id:
        deposit.submitted_by_id = user_id

    db.session.add(deposit)
    db.session.commit()
    db.session.refresh(deposit)

    return deposit


def post_deposit(deposit: "Deposit") -> "Deposit":
    """Post a submitted deposit.

    Args:
        deposit: Deposit instance to post

    Returns:
        Updated deposit instance

    Example:
        >>> deposit = DepositFactory(status="submitted")
        >>> deposit = post_deposit(deposit)
        >>> assert deposit.status == "posted"
    """
    from datetime import datetime

    from application.extensions import db

    if deposit.status != "submitted":
        raise ValueError("Can only post submitted deposits")

    deposit.status = "posted"
    deposit.posted = datetime.utcnow()

    db.session.add(deposit)
    db.session.commit()
    db.session.refresh(deposit)

    return deposit


def add_transaction_to_deposit(deposit: "Deposit", transaction: "Transaction") -> None:
    """Add a transaction to a deposit.

    Args:
        deposit: Deposit to add transaction to
        transaction: Transaction to add

    Example:
        >>> deposit = DepositFactory(status="draft")
        >>> txn = TransactionFactory(status="undeposited")
        >>> add_transaction_to_deposit(deposit, txn)
        >>> assert txn.deposit_id == deposit.id
    """
    from application.extensions import db

    transaction.deposit = deposit
    transaction.status = "deposited"

    db.session.add(transaction)
    db.session.commit()


def create_workflow_test_data() -> Dict[str, Any]:
    """Create a complete set of test data for workflow testing.

    Creates users, transactions, deposits, and other objects in various states.

    Returns:
        Dictionary with created objects

    Example:
        >>> data = create_workflow_test_data()
        >>> assert "admin" in data
        >>> assert "draft_transaction" in data
        >>> assert "submitted_transaction" in data
    """
    from tests.factories import (
        DepositFactory,
        UserFactory,
        create_complete_transaction,
    )
    from tests.helpers.auth_helpers import create_admin_user

    # Create users
    admin = create_admin_user()
    regular_user = UserFactory(user_name="regularuser")

    # Create transactions in various states
    draft_txn = create_complete_transaction(status="draft")
    submitted_txn = create_complete_transaction(status="submitted")
    cancelled_txn = create_complete_transaction(status="cancelled")

    # Create deposits
    draft_deposit = DepositFactory(status="draft")
    submitted_deposit = DepositFactory(status="submitted")

    return {
        "admin": admin,
        "regular_user": regular_user,
        "draft_transaction": draft_txn,
        "submitted_transaction": submitted_txn,
        "cancelled_transaction": cancelled_txn,
        "draft_deposit": draft_deposit,
        "submitted_deposit": submitted_deposit,
    }
