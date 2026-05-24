"""create audit log table

Revision ID: create_audit_log_table
Revises:
Create Date: 2026-05-23

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'create_audit_log_table'
down_revision = None  # Will be updated when run


def upgrade():
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('record_type', sa.String(length=50), nullable=False),
    sa.Column('record_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=50), nullable=False),
    sa.Column('old_values', sa.Text(), nullable=True),
    sa.Column('new_values', sa.Text(), nullable=True),
    sa.Column('changed_fields', sa.Text(), nullable=True),
    sa.Column('reason', sa.String(length=500), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('ip_address', sa.String(length=45), nullable=True),
    sa.Column('metadata', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for better query performance
    op.create_index('ix_audit_log_record', 'audit_log', ['record_type', 'record_id'])
    op.create_index('ix_audit_log_user', 'audit_log', ['user_id'])
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])
    op.create_index('ix_audit_log_action', 'audit_log', ['action'])


def downgrade():
    op.drop_index('ix_audit_log_action', table_name='audit_log')
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_user', table_name='audit_log')
    op.drop_index('ix_audit_log_record', table_name='audit_log')
    op.drop_table('audit_log')
