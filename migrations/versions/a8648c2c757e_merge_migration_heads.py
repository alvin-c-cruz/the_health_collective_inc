"""Merge migration heads

Revision ID: a8648c2c757e
Revises: d57d6eb765b4, ebf5c4598549
Create Date: 2026-06-04 11:28:50.014236

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a8648c2c757e'
down_revision = ('d57d6eb765b4', 'ebf5c4598549')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
