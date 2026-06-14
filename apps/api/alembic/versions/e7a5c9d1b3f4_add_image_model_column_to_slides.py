"""add image_model column to slides

Revision ID: e7a5c9d1b3f4
Revises: 3a2c33f7aa6c
Create Date: 2026-06-15 01:26:29.135789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e7a5c9d1b3f4'
down_revision: Union[str, Sequence[str], None] = '3a2c33f7aa6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('slides', sa.Column('image_model', sa.String(length=50), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('slides', 'image_model')
