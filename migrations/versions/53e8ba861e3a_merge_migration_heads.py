"""Merge migration heads

Revision ID: 53e8ba861e3a
Revises: add_cancellation_request_fields, create_audit_log_table
Create Date: 2026-05-23 17:37:27.543093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '53e8ba861e3a'
down_revision = ('add_cancellation_request_fields', 'create_audit_log_table')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
