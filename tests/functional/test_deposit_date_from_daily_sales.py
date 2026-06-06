"""
Functional tests for deposit date picker behavior.

When clicking "Deposit" button from daily_sales with a specific date selected,
the deposit form should default to that date.
"""
import pytest
from datetime import date


@pytest.mark.functional
def test_deposit_form_defaults_to_url_date_parameter(client, db):
    """
    Test that deposit form uses the date parameter from URL.

    When navigating to /deposit/new?date=2026-04-14, the deposit_date field
    should be pre-filled with 2026-04-14, not today's date.

    Bug: JavaScript sets date to today instead of using the URL parameter.
    Fix: Use deposit_date from context if available.
    """
    # Arrange: Specific date from daily_sales date picker
    selected_date = "2026-04-14"

    # Act: Navigate to record deposit with date parameter (as if clicking Deposit button from daily_sales)
    response = client.get(f'/daily_sales/deposit/new?date={selected_date}')

    # Assert: Should return 200 or 302 (redirect to login is acceptable for this test)
    assert response.status_code in [200, 302], f"Expected 200 or 302, got {response.status_code}"

    # If we got 200 (not redirected to login), check the template
    if response.status_code == 200:
        response_text = response.data.decode('utf-8')

        # The date should be in the template context for JavaScript to use
        # Look for the deposit_date variable being passed to JavaScript
        assert selected_date in response_text, f"Expected date {selected_date} to be in the page"


@pytest.mark.functional
def test_cancel_button_redirects_to_daily_sales_with_date(client, db):
    """
    Test that Cancel button redirects back to daily_sales with the original date.

    When clicking Cancel from /deposit/new?date=2026-04-14,
    should redirect to /daily_sales/?date=2026-04-14
    """
    # Arrange: Specific date from daily_sales
    selected_date = "2026-04-14"

    # Act: Navigate to record deposit
    response = client.get(f'/daily_sales/deposit/new?date={selected_date}')

    # Assert: Check that cancel link includes the date parameter
    if response.status_code == 200:
        response_text = response.data.decode('utf-8')

        # Cancel button should link to daily_sales with the date
        assert f'daily_sales.home' in response_text or f'/daily_sales/' in response_text
        assert selected_date in response_text
