import os
from datetime import timedelta
from http import HTTPStatus
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, session, url_for
from flask_login import current_user

from . import blueprints
from .blueprints.user import User
from .extensions import bcrypt, db, login_manager, mail, migrate
from .utils.version import get_version


def create_app(test=False):
    app = Flask(__name__, instance_relative_config=True)

    # Check if running in test mode via environment variable
    is_testing = test or os.environ.get("TESTING") == "1"

    if is_testing:
        # Use test configuration if available, otherwise load production and override
        try:
            app.config.from_pyfile("test_config.py")
        except FileNotFoundError:
            app.config.from_pyfile("config.py")
            # Override with test database from environment if set
            if "SQLALCHEMY_DATABASE_URI" in os.environ:
                app.config["SQLALCHEMY_DATABASE_URI"] = os.environ[
                    "SQLALCHEMY_DATABASE_URI"
                ]
    else:
        app.config.from_pyfile("config.py")

    app.config["REMEMBER_COOKIE_DURATION"] = timedelta(days=30)

    instance_path = Path(app.instance_path)
    parent_directory = Path(instance_path.parent)
    if not parent_directory.is_dir():
        parent_directory.mkdir()

    if not instance_path.is_dir():
        instance_path.mkdir()

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        if request.blueprint == "api":
            abort(HTTPStatus.UNAUTHORIZED)
        # Check maintenance mode before redirecting to login
        if app.config.get("MAINTENANCE_MODE", False):
            return redirect(url_for("maintenance"))
        return redirect(url_for("user.login"))

    # Maintenance page route
    @app.route("/maintenance")
    def maintenance():
        """Show maintenance page"""
        return render_template("maintenance.html"), 503

    # Maintenance mode check
    @app.before_request
    def check_maintenance_mode():
        # Skip maintenance check for maintenance page itself, static files, and login
        allowed_endpoints = ["maintenance", "user.login", "static"]
        if request.endpoint:
            if request.endpoint == "maintenance" or request.endpoint.startswith(
                "static"
            ):
                return None
            if request.endpoint == "user.login":
                return None

        # Check if maintenance mode is enabled
        if app.config.get("MAINTENANCE_MODE", False):
            # Check if user is a superuser using Flask-Login's current_user
            if current_user.is_authenticated:
                # Get user from database to check superuser status
                user = User.query.get(current_user.get_id())
                if user and user.superuser:
                    return None  # Superuser can access the site

            # Redirect everyone else to maintenance page
            return redirect(url_for("maintenance"))

        return None

    # Register Blueprints
    modules = [
        getattr(blueprints, module)
        for module in dir(blueprints)
        if hasattr(getattr(blueprints, module), "bp")
    ]

    menu_list = []
    for module in modules:
        app.register_blueprint(module.bp)
        if hasattr(module, "menu_label"):
            menu_list.append(module.menu_label)

    app.config["MENUS"] = menu_list

    # Initialize the database
    bcrypt.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    migrate.init_app(app=app, db=db)

    # Sync roles from registered modules on every startup
    # Skip during testing as tables may not exist yet
    if not os.environ.get("TESTING"):
        with app.app_context():
            from .blueprints.user.views import check_roles

            check_roles()

    # Register CSV Import blueprint
    from .blueprints.operations.daily_sales.csv_import_views import csv_import_bp

    app.register_blueprint(csv_import_bp)

    # Make version available to all templates
    @app.context_processor
    def inject_version():
        return {"app_version": get_version()}

    return app
