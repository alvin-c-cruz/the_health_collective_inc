"""
Pytest configuration and fixtures for The Health Collective Inc tests.
"""

import os
import sys

import pytest
from sqlalchemy.orm import scoped_session, sessionmaker

# Add application to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from application import create_app
from application.extensions import db as _db


@pytest.fixture(scope="session")
def app():
    """
    Create Flask application for testing.

    Scope: session (created once for all tests)

    CRITICAL: We MUST set the test database URI in environment BEFORE
    calling create_app() to prevent tests from using (and destroying!)
    the production database.
    """
    # Import here to avoid circular imports
    import os

    # CRITICAL: Set test database BEFORE create_app()
    os.environ["TESTING"] = "1"  # Signal to create_app to skip checks
    os.environ["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///:memory:"  # Use in-memory test DB
    )

    app = create_app()

    # Test configuration - redundant but explicit
    app.config.update(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",  # In-memory DB for speed
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
            "SECRET_KEY": "test-secret-key-do-not-use-in-production",
        }
    )

    # Create tables in the test database
    with app.app_context():
        _db.create_all()

    return app


@pytest.fixture(scope="session")
def _engine(app):
    """
    Create database engine.

    Scope: session (one engine for all tests)
    """
    with app.app_context():
        yield _db.engine
        # Clean up after all tests
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app, _engine):
    """
    Provide database session with transaction rollback.

    Scope: function (fresh session for each test)

    This uses the "nested transaction" pattern:
    - Begin a transaction
    - Run the test
    - Rollback the transaction (discarding all changes)

    This ensures each test starts with a clean database.
    """
    connection = _engine.connect()
    transaction = connection.begin()

    # Bind session to this connection
    session = scoped_session(
        sessionmaker(
            bind=connection,
            expire_on_commit=False,  # Don't expire objects after commit
        )
    )

    # Replace db.session with our test session
    _db.session = session

    yield session

    # Cleanup
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(app):
    """
    Provide Flask test client for making HTTP requests.
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Provide Flask CLI test runner.
    """
    return app.test_cli_runner()


@pytest.fixture(autouse=True)
def reset_db_session(db):
    """
    Automatically reset database session for each test.

    This fixture runs automatically for every test.
    """
    # Bind factories to this session
    try:
        from tests.factories import bind_factories

        bind_factories(db)
    except ImportError:
        # Factories not yet created, that's fine
        pass

    yield

    # Cleanup happens automatically due to transaction rollback in db fixture
