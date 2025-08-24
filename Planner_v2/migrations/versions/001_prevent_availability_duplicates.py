"""Add unique constraint to prevent duplicate availability records

Revision ID: prevent_availability_duplicates
Revises: [previous_revision]
Create Date: 2025-08-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'prevent_availability_duplicates'
down_revision = None  # Update this to the actual previous revision
branch_labels = None
depends_on = None

def upgrade():
    """Add unique constraint to prevent duplicate availability records"""
    # Create unique constraint on (guest_id, event_id, date)
    # This prevents the same guest from having multiple availability records for the same date in the same event
    op.create_unique_constraint(
        'uq_availability_guest_event_date',
        'availability',
        ['guest_id', 'event_id', 'date']
    )

def downgrade():
    """Remove the unique constraint"""
    op.drop_constraint('uq_availability_guest_event_date', 'availability', type_='unique')
