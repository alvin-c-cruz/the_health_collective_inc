"""Authentication and authorization test helpers.

Provides utilities for logging in users, creating users with specific roles,
and testing role-based access control.
"""

from typing import List, Optional

from flask.testing import FlaskClient


def login_user(
    client: FlaskClient, username: str = "testuser", password: str = "testpass123"
) -> None:
    """Log in a user via the test client.

    Args:
        client: Flask test client
        username: Username to log in with
        password: Password to use

    Example:
        >>> login_user(client, "admin", "admin123")
        >>> response = client.get("/dashboard")
        >>> assert response.status_code == 200
    """
    client.post(
        "/user/login",
        data={"user_name": username, "pass_word": password},
        follow_redirects=True,
    )


def logout_user(client: FlaskClient) -> None:
    """Log out the currently logged-in user.

    Args:
        client: Flask test client

    Example:
        >>> logout_user(client)
        >>> response = client.get("/dashboard")
        >>> assert response.status_code == 302  # Redirect to login
    """
    client.get("/user/logout", follow_redirects=True)


def create_user_with_roles(
    username: str,
    roles: List[str],
    password: str = "testpass123",
    active: bool = True,
    **kwargs,
) -> "User":
    """Create a user with specific roles.

    Args:
        username: Username for the new user
        roles: List of role names to assign
        password: Password for the user
        active: Whether the user is active
        **kwargs: Additional user attributes

    Returns:
        Created User instance

    Example:
        >>> user = create_user_with_roles(
        ...     "accountant",
        ...     ["Account", "Trial Balance", "Ledger"],
        ...     email="accountant@example.com"
        ... )
        >>> assert len(user.user_roles) == 3
    """
    from application.extensions import db
    from tests.factories import RoleFactory, UserFactory, UserRoleFactory

    # Create user
    user = UserFactory(user_name=username, active=active, **kwargs)
    user.set_pass_word(password)
    db.session.add(user)
    db.session.flush()

    # Create and assign roles
    for role_name in roles:
        # Try to get existing role first
        from application.blueprints.user.models import Role

        role = db.session.query(Role).filter_by(name=role_name).first()

        if not role:
            # Create role if it doesn't exist
            role = RoleFactory(name=role_name)
            db.session.add(role)
            db.session.flush()

        # Assign role to user
        user_role = UserRoleFactory(user_id=user.id, role_id=role.id)
        db.session.add(user_role)

    db.session.commit()
    return user


def create_admin_user(username: str = "admin", password: str = "admin123") -> "User":
    """Create an admin user with all permissions.

    Args:
        username: Username for the admin
        password: Password for the admin

    Returns:
        Created admin User instance

    Example:
        >>> admin = create_admin_user()
        >>> assert admin.admin is True
        >>> assert admin.superuser is True
    """
    from application.extensions import db
    from tests.factories import UserFactory

    user = UserFactory(
        user_name=username,
        admin=True,
        superuser=True,
        active=True,
    )
    user.set_pass_word(password)
    db.session.add(user)
    db.session.commit()
    return user


def login_as_user_with_roles(
    client: FlaskClient, roles: List[str], username: Optional[str] = None
) -> "User":
    """Create a user with specific roles and log them in.

    Convenience function that combines create_user_with_roles and login_user.

    Args:
        client: Flask test client
        roles: List of role names
        username: Optional username (generated if not provided)

    Returns:
        Created and logged-in User instance

    Example:
        >>> user = login_as_user_with_roles(client, ["Daily Sales", "Collections"])
        >>> response = client.get("/daily_sales/")
        >>> assert response.status_code == 200
    """
    if username is None:
        import random

        username = f"testuser_{random.randint(1000, 9999)}"

    user = create_user_with_roles(username, roles)
    login_user(client, username)
    return user


def has_permission(user: "User", role_name: str) -> bool:
    """Check if a user has a specific role/permission.

    Args:
        user: User instance to check
        role_name: Role name to check for

    Returns:
        True if user has the role, False otherwise

    Example:
        >>> assert has_permission(user, "Daily Sales")
        >>> assert not has_permission(user, "Admin Only Feature")
    """
    return any(ur.role.name == role_name for ur in user.user_roles)
