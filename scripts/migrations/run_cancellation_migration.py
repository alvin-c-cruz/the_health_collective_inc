#!/usr/bin/env python
"""
Run pending Alembic migrations for cancellation request fields
"""
from application import create_app
from application.extensions import db
from alembic import command
from alembic.config import Config

app = create_app()

with app.app_context():
    alembic_cfg = Config('migrations/alembic.ini')
    alembic_cfg.set_main_option('script_location', 'migrations')

    print("Running migration to add cancellation request fields...")
    command.upgrade(alembic_cfg, 'head')
    print("Migration completed successfully!")
