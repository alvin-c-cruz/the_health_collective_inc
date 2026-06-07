"""Test helper utilities.

This package provides reusable helper functions for testing to reduce
boilerplate and make tests more readable.

Available helpers:
- auth_helpers: Authentication and authorization testing
- workflow_helpers: Common workflow testing (submit, approve, cancel)
- assertion_helpers: Custom assertions for complex objects
"""

from .assertion_helpers import (
    assert_audit_log_exists,
    assert_flash_message,
    assert_redirect_to,
    assert_status_code,
)
from .auth_helpers import create_user_with_roles, login_user, logout_user
from .workflow_helpers import (
    approve_transaction,
    cancel_transaction,
    create_and_submit_transaction,
    submit_transaction,
)

__all__ = [
    # Auth helpers
    "login_user",
    "logout_user",
    "create_user_with_roles",
    # Workflow helpers
    "submit_transaction",
    "approve_transaction",
    "cancel_transaction",
    "create_and_submit_transaction",
    # Assertion helpers
    "assert_audit_log_exists",
    "assert_status_code",
    "assert_flash_message",
    "assert_redirect_to",
]
