"""
Approval Helper Functions for Transaction Management

These functions ensure that BOTH the legacy (AdminTransaction) and new workflow
(approved_at, approved_by_id, status) systems are kept in sync.

ALWAYS use these helpers when approving/unapproving transactions to avoid
dual-system conflicts where the UI and queries become inconsistent.

Created: 2026-06-04
Issue: Approved transactions not appearing in deposits/collections
See: docs/the_health_collective_inc/PREVENTING_DUAL_SYSTEM_CONFLICTS.md
"""

from datetime import datetime
import logging

from .admin_models import AdminTransaction
from application.extensions import db

logger = logging.getLogger(__name__)


def approve_transaction_both_systems(transaction, user_id):
    """
    Approve a transaction in BOTH legacy and new systems.
    This ensures UI and queries stay consistent.

    Args:
        transaction: Transaction object to approve
        user_id: ID of user approving the transaction

    Returns:
        bool: True if successful, False if already approved

    Example:
        >>> from .models import Transaction
        >>> from flask_login import current_user
        >>> txn = Transaction.query.get(123)
        >>> success = approve_transaction_both_systems(txn, current_user.id)
        >>> if success:
        >>>     db.session.commit()
    """
    # Check if already approved (either system)
    existing_admin = AdminTransaction.query.filter_by(transaction_id=transaction.id).first()
    if existing_admin:
        logger.warning(
            f"Transaction {transaction.id} already has AdminTransaction record"
        )
        return False

    if transaction.approved_at:
        logger.warning(
            f"Transaction {transaction.id} already has approved_at set"
        )
        return False

    # Update BOTH systems atomically
    # 1. Legacy system (for backward compatibility)
    admin_record = AdminTransaction(
        transaction_id=transaction.id,
        user_id=user_id,
    )
    db.session.add(admin_record)

    # 2. New workflow system
    transaction.approved_at = datetime.utcnow()
    transaction.approved_by_id = user_id
    transaction.status = 'posted'  # Approved transactions are posted

    logger.info(
        f"Transaction {transaction.id} approved by user {user_id} in both systems"
    )

    return True


def unapprove_transaction_both_systems(transaction):
    """
    Remove approval from BOTH legacy and new systems.

    Args:
        transaction: Transaction object to unapprove

    Returns:
        bool: True if successful, False if not approved

    Example:
        >>> from .models import Transaction
        >>> txn = Transaction.query.get(123)
        >>> success = unapprove_transaction_both_systems(txn)
        >>> if success:
        >>>     db.session.commit()
    """
    # Check if approved
    existing_admin = AdminTransaction.query.filter_by(transaction_id=transaction.id).first()

    if not existing_admin and not transaction.approved_at:
        logger.warning(
            f"Transaction {transaction.id} is not approved in either system"
        )
        return False

    # Detect mismatch before clearing
    if (existing_admin is not None) != (transaction.approved_at is not None):
        logger.error(
            f"SYNC ISSUE: Transaction {transaction.id} - "
            f"Legacy approved: {existing_admin is not None}, "
            f"New approved: {transaction.approved_at is not None}"
        )

    # Clear BOTH systems atomically
    # 1. Legacy system
    if existing_admin:
        AdminTransaction.query.filter_by(transaction_id=transaction.id).delete()

    # 2. New workflow system
    transaction.approved_at = None
    transaction.approved_by_id = None
    transaction.status = 'draft'  # Return to draft status

    logger.info(
        f"Transaction {transaction.id} approval removed from both systems"
    )

    return True


def is_transaction_approved(transaction):
    """
    Check if transaction is approved (checks both systems for safety).
    Logs warning if systems are out of sync.

    Args:
        transaction: Transaction object to check

    Returns:
        bool: True if approved in either system

    Example:
        >>> from .models import Transaction
        >>> txn = Transaction.query.get(123)
        >>> if is_transaction_approved(txn):
        >>>     print("Transaction is approved")
    """
    legacy_approved = AdminTransaction.query.filter_by(
        transaction_id=transaction.id
    ).first() is not None

    new_approved = transaction.approved_at is not None

    # Log warning if systems are out of sync
    if legacy_approved != new_approved:
        logger.error(
            f"APPROVAL MISMATCH: Transaction {transaction.id} (#{transaction.record_number}) - "
            f"Legacy: {legacy_approved}, New: {new_approved}. "
            f"Systems are out of sync! Run migration script."
        )

    return legacy_approved or new_approved


def get_approved_by_user(transaction):
    """
    Get the user who approved this transaction.
    Tries new workflow first, falls back to legacy.

    Args:
        transaction: Transaction object

    Returns:
        User object or None

    Example:
        >>> from .models import Transaction
        >>> txn = Transaction.query.get(123)
        >>> user = get_approved_by_user(txn)
        >>> if user:
        >>>     print(f"Approved by: {user.user_name}")
    """
    # Try new workflow first
    if transaction.approved_by_id:
        from application.blueprints.user.models import User
        return User.query.get(transaction.approved_by_id)

    # Fall back to legacy system
    admin_record = AdminTransaction.query.filter_by(
        transaction_id=transaction.id
    ).first()

    if admin_record:
        from application.blueprints.user.models import User
        logger.warning(
            f"Transaction {transaction.id} using legacy approval user. "
            f"Consider running migration."
        )
        return User.query.get(admin_record.user_id)

    return None


def sync_check_all_transactions():
    """
    Utility function to check all transactions for sync issues.
    Returns list of transaction IDs with mismatches.

    This is useful for periodic health checks or after migrations.

    Returns:
        list: Transaction IDs with sync issues

    Example:
        >>> mismatches = sync_check_all_transactions()
        >>> if mismatches:
        >>>     print(f"Found {len(mismatches)} transactions out of sync")
        >>>     print(f"IDs: {mismatches}")
    """
    from .models import Transaction

    # Get all AdminTransaction records
    admin_txns = AdminTransaction.query.all()
    admin_ids = {admin.transaction_id for admin in admin_txns}

    # Get all transactions with approved_at set
    approved_txns = Transaction.query.filter(
        Transaction.approved_at.isnot(None)
    ).all()
    approved_ids = {txn.id for txn in approved_txns}

    # Find mismatches
    only_in_legacy = admin_ids - approved_ids
    only_in_new = approved_ids - admin_ids

    mismatches = list(only_in_legacy | only_in_new)

    if mismatches:
        logger.error(
            f"Found {len(mismatches)} transactions with sync issues. "
            f"Only in legacy: {len(only_in_legacy)}, "
            f"Only in new: {len(only_in_new)}"
        )

    return mismatches
