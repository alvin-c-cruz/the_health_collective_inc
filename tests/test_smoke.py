"""
Smoke tests to verify test infrastructure is working.

These tests should ALWAYS pass if the setup is correct.
"""
import pytest


def test_app_exists(app):
    """Smoke test: Flask app can be created."""
    assert app is not None


def test_app_is_testing(app):
    """Smoke test: App is in testing mode."""
    assert app.config['TESTING'] is True


def test_database_connection(db):
    """Smoke test: Database connection works."""
    assert db is not None


def test_client_can_make_request(client):
    """Smoke test: Test client can make HTTP requests."""
    response = client.get('/')
    # Should return 200 or 404, but not error
    assert response.status_code in [200, 404, 302]


def test_import_application():
    """Smoke test: Can import application module."""
    from application import create_app
    app = create_app()
    assert app is not None


def test_import_models():
    """Smoke test: Can import models."""
    try:
        from application.blueprints.operations.daily_sales.models import Transaction, Deposit
        assert Transaction is not None
        assert Deposit is not None
    except ImportError as e:
        pytest.fail(f"Failed to import models: {e}")


def test_database_tables_exist(app, db):
    """Smoke test: Database tables are created."""
    with app.app_context():
        from application.extensions import db as _db

        # Check if tables exist
        inspector = _db.inspect(_db.engine)
        tables = inspector.get_table_names()

        # Should have at least some tables
        assert len(tables) > 0, "No tables found in database"


@pytest.mark.parametrize("test_value,expected", [
    (1 + 1, 2),
    ("hello" + " world", "hello world"),
    ([1, 2] + [3], [1, 2, 3]),
])
def test_pytest_parametrize_works(test_value, expected):
    """Smoke test: Pytest parametrize works."""
    assert test_value == expected
