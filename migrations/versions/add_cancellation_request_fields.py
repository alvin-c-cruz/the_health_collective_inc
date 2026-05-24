"""Add cancellation request fields to transaction

Revision ID: add_cancellation_request_fields
Revises: add_customer_name_fields
Create Date: 2026-05-23 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_cancellation_request_fields'
down_revision = 'add_customer_name_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add cancellation request fields to transaction table
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.add_column(sa.Column('cancellation_requested_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('cancellation_requested_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('cancellation_reason', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('cancellation_approved_by_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('cancellation_approved_at', sa.DateTime(), nullable=True))

        batch_op.create_foreign_key('fk_transaction_cancel_requested_by', 'user', ['cancellation_requested_by_id'], ['id'])
        batch_op.create_foreign_key('fk_transaction_cancel_approved_by', 'user', ['cancellation_approved_by_id'], ['id'])


def downgrade():
    with op.batch_alter_table('transaction', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transaction_cancel_approved_by', type_='foreignkey')
        batch_op.drop_constraint('fk_transaction_cancel_requested_by', type_='foreignkey')
        batch_op.drop_column('cancellation_approved_at')
        batch_op.drop_column('cancellation_approved_by_id')
        batch_op.drop_column('cancellation_reason')
        batch_op.drop_column('cancellation_requested_at')
        batch_op.drop_column('cancellation_requested_by_id')
