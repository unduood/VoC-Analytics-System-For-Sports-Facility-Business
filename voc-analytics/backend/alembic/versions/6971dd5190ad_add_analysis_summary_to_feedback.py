"""add_analysis_summary_to_feedback

Revision ID: 6971dd5190ad
Revises: 197265c769fa
Create Date: 2026-01-07 23:04:44.619794

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = '6971dd5190ad'
down_revision: Union[str, None] = '197265c769fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add analysis_summary JSONB column to feedback_records
    for storing ML analysis results summary (quick dashboard access)
    """
    op.add_column(
        'feedback_records',
        sa.Column('analysis_summary', JSONB, nullable=True, comment='ML analysis results summary')
    )

    # Create GIN index for JSONB queries (optional but recommended for performance)
    op.create_index(
        'idx_feedback_analysis_summary',
        'feedback_records',
        ['analysis_summary'],
        postgresql_using='gin'
    )


def downgrade() -> None:
    """
    Remove analysis_summary column
    """
    op.drop_index('idx_feedback_analysis_summary', table_name='feedback_records')
    op.drop_column('feedback_records', 'analysis_summary')
