"""add_original_source_to_analysis_tables

Revision ID: a1b2c3d4e5f6
Revises: 92cb609282f1
Create Date: 2026-01-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '92cb609282f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add original_source column to all three analysis tables.

    Tracks the pre-edit source (model or rating) so that reverting
    a user correction restores the correct source — not always 'model'.
    """

    # 1. sentiment_results
    op.add_column('sentiment_results',
        sa.Column('original_source', sa.String(20), nullable=True,
                  comment='Original source before user edit (model, rating)'))

    # 2. intent_results
    op.add_column('intent_results',
        sa.Column('original_source', sa.String(20), nullable=True,
                  comment='Original source before user edit (model, rating)'))

    # 3. aspect_sentiment_results
    op.add_column('aspect_sentiment_results',
        sa.Column('original_source', sa.String(20), nullable=True,
                  comment='Original source before user edit (model, rating)'))


def downgrade() -> None:
    """Remove original_source columns"""
    op.drop_column('aspect_sentiment_results', 'original_source')
    op.drop_column('intent_results', 'original_source')
    op.drop_column('sentiment_results', 'original_source')
