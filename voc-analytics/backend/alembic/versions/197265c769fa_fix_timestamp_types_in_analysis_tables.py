"""fix_timestamp_types_in_analysis_tables

Revision ID: 197265c769fa
Revises: e7dd65e74927
Create Date: 2026-01-07 19:43:24.501574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '197265c769fa'
down_revision: Union[str, None] = 'e7dd65e74927'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Change created_at column type from String to TIMESTAMP(timezone=True)
    in sentiment_results, intent_results, and aspect_sentiment_results tables
    """
    # Fix sentiment_results.created_at
    op.execute("""
        ALTER TABLE sentiment_results
        ALTER COLUMN created_at DROP DEFAULT
    """)
    op.execute("""
        ALTER TABLE sentiment_results
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING CASE
            WHEN created_at = 'NOW()' THEN NOW()
            ELSE created_at::timestamp with time zone
        END
    """)
    op.execute("""
        ALTER TABLE sentiment_results
        ALTER COLUMN created_at SET DEFAULT NOW()
    """)

    # Fix intent_results.created_at
    op.execute("""
        ALTER TABLE intent_results
        ALTER COLUMN created_at DROP DEFAULT
    """)
    op.execute("""
        ALTER TABLE intent_results
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING CASE
            WHEN created_at = 'NOW()' THEN NOW()
            ELSE created_at::timestamp with time zone
        END
    """)
    op.execute("""
        ALTER TABLE intent_results
        ALTER COLUMN created_at SET DEFAULT NOW()
    """)

    # Fix aspect_sentiment_results.created_at
    op.execute("""
        ALTER TABLE aspect_sentiment_results
        ALTER COLUMN created_at DROP DEFAULT
    """)
    op.execute("""
        ALTER TABLE aspect_sentiment_results
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING CASE
            WHEN created_at = 'NOW()' THEN NOW()
            ELSE created_at::timestamp with time zone
        END
    """)
    op.execute("""
        ALTER TABLE aspect_sentiment_results
        ALTER COLUMN created_at SET DEFAULT NOW()
    """)


def downgrade() -> None:
    """
    Revert created_at column type from TIMESTAMP to String
    (for rollback purposes - not recommended in production)
    """
    # Revert sentiment_results.created_at
    op.execute("""
        ALTER TABLE sentiment_results
        ALTER COLUMN created_at TYPE VARCHAR
        USING created_at::varchar
    """)

    # Revert intent_results.created_at
    op.execute("""
        ALTER TABLE intent_results
        ALTER COLUMN created_at TYPE VARCHAR
        USING created_at::varchar
    """)

    # Revert aspect_sentiment_results.created_at
    op.execute("""
        ALTER TABLE aspect_sentiment_results
        ALTER COLUMN created_at TYPE VARCHAR
        USING created_at::varchar
    """)
