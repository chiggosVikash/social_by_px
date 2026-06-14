"""make_article_url_unique_per_project

Revision ID: 3a2c33f7aa6c
Revises: 9096cebbd688
Create Date: 2026-06-14 18:34:52.221881

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a2c33f7aa6c'
down_revision: Union[str, Sequence[str], None] = '9096cebbd688'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the global unique constraint on the 'url' column in table 'articles'
    op.drop_constraint('articles_url_key', 'articles', type_='unique')
    
    # Add a composite unique constraint on (project_id, url)
    op.create_unique_constraint('uq_article_project_url', 'articles', ['project_id', 'url'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the composite unique constraint
    op.drop_constraint('uq_article_project_url', 'articles', type_='unique')
    
    # Add back the global unique constraint on 'url'
    op.create_unique_constraint('articles_url_key', 'articles', ['url'])
