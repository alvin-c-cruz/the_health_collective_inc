"""Create centralized audit trail tables

Revision ID: ebf5c4598549
Revises: feb9b1347ce1
Create Date: 2026-06-04 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebf5c4598549'
down_revision = 'feb9b1347ce1'
branch_labels = None
depends_on = None


def upgrade():
    """
    Create centralized audit_logs and login_history tables.

    This migration creates the new centralized audit trail system
    that will be used across all modules.
    """

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),

        # Record identification
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('record_id', sa.Integer(), nullable=True),
        sa.Column('record_identifier', sa.String(length=200), nullable=True),

        # Who made the change (with denormalization for safety)
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=80), nullable=True),
        sa.Column('full_name', sa.String(length=200), nullable=True),

        # When (Philippine time)
        sa.Column('timestamp', sa.DateTime(), nullable=False),

        # What changed (JSON storage)
        sa.Column('old_values', sa.Text(), nullable=True),
        sa.Column('new_values', sa.Text(), nullable=True),

        # Where/How
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),

        # Additional context
        sa.Column('reason', sa.String(length=500), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),

        # Constraints
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for audit_logs
    op.create_index('ix_audit_logs_module', 'audit_logs', ['module'])
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
    op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])

    # Create login_history table
    op.create_table('login_history',
        sa.Column('id', sa.Integer(), nullable=False),

        # User information (denormalized)
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('full_name', sa.String(length=200), nullable=True),

        # Login details
        sa.Column('login_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('failure_reason', sa.String(length=200), nullable=True),

        # Where/How
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),

        # Constraints
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for login_history
    op.create_index('ix_login_history_user_id', 'login_history', ['user_id'])
    op.create_index('ix_login_history_login_time', 'login_history', ['login_time'])
    op.create_index('ix_login_history_status', 'login_history', ['status'])


def downgrade():
    """
    Remove centralized audit trail tables.

    WARNING: This will delete all audit and login history data!
    """
    # Drop login_history table
    op.drop_index('ix_login_history_status', 'login_history')
    op.drop_index('ix_login_history_login_time', 'login_history')
    op.drop_index('ix_login_history_user_id', 'login_history')
    op.drop_table('login_history')

    # Drop audit_logs table
    op.drop_index('ix_audit_logs_timestamp', 'audit_logs')
    op.drop_index('ix_audit_logs_user_id', 'audit_logs')
    op.drop_index('ix_audit_logs_action', 'audit_logs')
    op.drop_index('ix_audit_logs_module', 'audit_logs')
    op.drop_table('audit_logs')
