"""Add text_zone, visual_type columns to Slide, and style_preset to Project

Revision ID: 20240615_1a2b3c4d
Revises: 3a2c33f7aa6c
Create Date: 2024-06-15 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '20240615_1a2b3c4d'
down_revision = '3a2c33f7aa6c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add style_preset to Project table (nullable, default 'general_soft')
    op.add_column('project',
        sa.Column('style_preset', sa.String(32), nullable=True,
                 server_default='general_soft')
    )

    # Add text_zone and visual_type to Slide table (nullable, default values)
    op.add_column('slide',
        sa.Column('text_zone', sa.String(32), nullable=True,
                 server_default='center-bottom third')
    )
    op.add_column('slide',
        sa.Column('visual_type', sa.String(16), nullable=True,
                 server_default='minimalist')
    )


def downgrade() -> None:
    op.drop_column('slide', 'visual_type')
    op.drop_column('slide', 'text_zone')
    op.drop_column('project', 'style_preset')
