"""Add last_name, first_name, middle_name to customer

Revision ID: add_customer_name_fields
Revises: d91b7dbeff1c
Create Date: 2026-05-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_customer_name_fields'
down_revision = '18122d455907'
branch_labels = None
depends_on = None


def upgrade():
    # Add new name fields to customer table
    op.add_column('customer', sa.Column('last_name', sa.String(length=100), nullable=True))
    op.add_column('customer', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('customer', sa.Column('middle_name', sa.String(length=100), nullable=True))


def downgrade():
    # Remove name fields
    op.drop_column('customer', 'middle_name')
    op.drop_column('customer', 'first_name')
    op.drop_column('customer', 'last_name')
