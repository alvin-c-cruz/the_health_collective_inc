"""Add display_name to bank_account

Revision ID: e6508171b56c
Revises: a8648c2c757e
Create Date: 2026-06-04 11:29:08.064514

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e6508171b56c'
down_revision = 'a8648c2c757e'
branch_labels = None
depends_on = None


def upgrade():
    # Add display_name column to bank_account table
    op.add_column('bank_account', sa.Column('display_name', sa.String(length=500), nullable=True))

    # Populate existing records with default display format
    op.execute("""
        UPDATE bank_account
        SET display_name = bank_name || ' — ' || account_number
        WHERE display_name IS NULL
    """)


def downgrade():
    # Remove display_name column
    op.drop_column('bank_account', 'display_name')
