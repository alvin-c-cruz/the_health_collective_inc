"""Custom assertion helpers for testing.

Provides readable assertions for common testing patterns like checking
flash messages, redirects, audit logs, and status codes.
"""

from typing import Optional, List
from flask import get_flashed_messages
from flask.testing import FlaskClient


def assert_status_code(response, expected_code: int, message: Optional[str] = None):
    """Assert that response has expected status code.

    Args:
        response: Flask response object
        expected_code: Expected HTTP status code
        message: Optional custom error message

    Example:
        >>> response = client.get("/dashboard")
        >>> assert_status_code(response, 200)
    """
    if response.status_code != expected_code:
        error_msg = (
            message
            or f"Expected status code {expected_code}, got {response.status_code}"
        )
        raise AssertionError(error_msg)


def assert_flash_message(
    expected_message: str,
    category: Optional[str] = None,
    partial: bool = False,
):
    """Assert that a flash message was set.

    Args:
        expected_message: Expected flash message text
        category: Expected message category (success, error, info, warning)
        partial: If True, checks if expected_message is substring of actual

    Example:
        >>> client.post("/transaction/submit", data={...})
        >>> assert_flash_message("Transaction submitted successfully", category="success")
    """
    messages = get_flashed_messages(with_categories=True)

    if not messages:
        raise AssertionError(f"No flash messages found. Expected: '{expected_message}'")

    # Check messages
    found = False
    for msg_category, msg_text in messages:
        if partial:
            text_match = expected_message in msg_text
        else:
            text_match = expected_message == msg_text

        category_match = category is None or msg_category == category

        if text_match and category_match:
            found = True
            break

    if not found:
        actual_messages = [f"({cat}) {msg}" for cat, msg in messages]
        raise AssertionError(
            f"Flash message not found.\n"
            f"Expected: ({category or 'any'}) '{expected_message}'\n"
            f"Actual messages: {actual_messages}"
        )


def assert_redirect_to(response, expected_location: str, partial: bool = False):
    """Assert that response is a redirect to expected location.

    Args:
        response: Flask response object
        expected_location: Expected redirect location
        partial: If True, checks if expected_location is in actual location

    Example:
        >>> response = client.post("/login", data={...})
        >>> assert_redirect_to(response, "/dashboard")
    """
    if response.status_code not in (301, 302, 303, 307, 308):
        raise AssertionError(
            f"Expected redirect (3xx), got status code {response.status_code}"
        )

    actual_location = response.location or ""

    if partial:
        if expected_location not in actual_location:
            raise AssertionError(
                f"Expected redirect to contain '{expected_location}', "
                f"got '{actual_location}'"
            )
    else:
        if not actual_location.endswith(expected_location):
            raise AssertionError(
                f"Expected redirect to '{expected_location}', "
                f"got '{actual_location}'"
            )


def assert_audit_log_exists(
    model_name: str,
    action: str,
    user_id: Optional[int] = None,
    record_id: Optional[int] = None,
):
    """Assert that an audit log entry exists.

    Args:
        model_name: Name of the model (e.g., "Transaction", "Deposit")
        action: Action performed (e.g., "create", "update", "delete")
        user_id: Optional user ID to check
        record_id: Optional record ID to check

    Example:
        >>> txn = TransactionFactory()
        >>> assert_audit_log_exists("Transaction", "create", record_id=txn.id)
    """
    from application.blueprints.audit.models import AuditLog
    from application.extensions import db

    query = db.session.query(AuditLog).filter(
        AuditLog.model_name == model_name, AuditLog.action == action
    )

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if record_id is not None:
        query = query.filter(AuditLog.record_id == record_id)

    audit_log = query.first()

    if not audit_log:
        filters = [f"model='{model_name}'", f"action='{action}'"]
        if user_id:
            filters.append(f"user_id={user_id}")
        if record_id:
            filters.append(f"record_id={record_id}")

        raise AssertionError(
            f"No audit log found with filters: {', '.join(filters)}"
        )


def assert_template_used(response, template_name: str):
    """Assert that a specific template was used to render the response.

    Args:
        response: Flask response object
        template_name: Name of template that should have been used

    Example:
        >>> response = client.get("/dashboard")
        >>> assert_template_used(response, "dashboard/home.html")
    """
    # Note: This requires Flask-DebugToolbar or similar in test mode
    # For now, we'll check the response data for template markers
    if hasattr(response, "template"):
        actual_template = response.template.name if response.template else None
        if actual_template != template_name:
            raise AssertionError(
                f"Expected template '{template_name}', got '{actual_template}'"
            )
    else:
        # Fallback: just check if template name appears in response
        if template_name.encode() not in response.data:
            raise AssertionError(
                f"Template '{template_name}' not found in response "
                "(note: limited check without template recording)"
            )


def assert_contains(response, text: str, case_sensitive: bool = True):
    """Assert that response contains specific text.

    Args:
        response: Flask response object
        text: Text to search for
        case_sensitive: Whether search should be case-sensitive

    Example:
        >>> response = client.get("/dashboard")
        >>> assert_contains(response, "Total Sales")
    """
    response_data = response.data.decode("utf-8")

    if not case_sensitive:
        text = text.lower()
        response_data = response_data.lower()

    if text not in response_data:
        raise AssertionError(
            f"Response does not contain '{text}'\n"
            f"Response preview: {response_data[:500]}"
        )


def assert_not_contains(response, text: str, case_sensitive: bool = True):
    """Assert that response does NOT contain specific text.

    Args:
        response: Flask response object
        text: Text to check is absent
        case_sensitive: Whether search should be case-sensitive

    Example:
        >>> response = client.get("/dashboard")
        >>> assert_not_contains(response, "Error:")
    """
    response_data = response.data.decode("utf-8")

    if not case_sensitive:
        text = text.lower()
        response_data = response_data.lower()

    if text in response_data:
        # Find context around the text
        index = response_data.find(text)
        start = max(0, index - 50)
        end = min(len(response_data), index + len(text) + 50)
        context = response_data[start:end]

        raise AssertionError(
            f"Response should not contain '{text}'\n" f"Found at: ...{context}..."
        )


def assert_count(items: List, expected_count: int, item_description: str = "items"):
    """Assert that a list has expected number of items.

    Args:
        items: List to check
        expected_count: Expected number of items
        item_description: Description of items for error message

    Example:
        >>> transactions = Transaction.query.all()
        >>> assert_count(transactions, 5, "transactions")
    """
    actual_count = len(items)
    if actual_count != expected_count:
        raise AssertionError(
            f"Expected {expected_count} {item_description}, got {actual_count}"
        )


def assert_approx_equal(
    actual: float, expected: float, tolerance: float = 0.01, description: str = "value"
):
    """Assert that two floats are approximately equal.

    Useful for currency calculations where floating point precision matters.

    Args:
        actual: Actual value
        expected: Expected value
        tolerance: Acceptable difference (default 0.01 for currency)
        description: Description for error message

    Example:
        >>> total = calculate_total(items)
        >>> assert_approx_equal(total, 1234.56, description="transaction total")
    """
    if abs(actual - expected) > tolerance:
        raise AssertionError(
            f"Expected {description} to be approximately {expected}, "
            f"got {actual} (tolerance: {tolerance})"
        )
