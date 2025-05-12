"""Add reviews table

Revision ID: 3a19723896fd
Revises: 80ca8b87274d
Create Date: 2025-05-12 10:52:48.562077

"""
"""Allow nullable user_id on reviews"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '7de0806500f8'
down_revision = '3a19723896fd'
branch_labels = None
depends_on = None

def upgrade():
    # Make reviews.user_id nullable
    op.alter_column(
        'reviews',
        'user_id',
        existing_type=sa.Integer(),
        nullable=True,
    )

def downgrade():
    # Revert to non-nullable
    op.alter_column(
        'reviews',
        'user_id',
        existing_type=sa.Integer(),
        nullable=False,
    )