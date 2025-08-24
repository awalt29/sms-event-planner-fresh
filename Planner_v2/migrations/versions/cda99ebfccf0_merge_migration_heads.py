"""Merge migration heads

Revision ID: cda99ebfccf0
Revises: prevent_availability_duplicates, 6ba344f582b6
Create Date: 2025-08-16 17:22:28.821969

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cda99ebfccf0'
down_revision = ('prevent_availability_duplicates', '6ba344f582b6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
