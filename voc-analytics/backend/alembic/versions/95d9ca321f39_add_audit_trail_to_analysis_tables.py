"""add_audit_trail_to_analysis_tables

Revision ID: 95d9ca321f39
Revises: 6971dd5190ad
Create Date: 2026-01-08 02:28:59.407076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95d9ca321f39'
down_revision: Union[str, None] = '6971dd5190ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add audit trail columns to analysis tables for tracking:
    - Model predictions vs user corrections
    - Edit history (1-level undo)
    - Soft deletes
    """

    # ===== 1. sentiment_results =====
    op.add_column('sentiment_results',
        sa.Column('source', sa.String(20), nullable=False, server_default='model',
                  comment='Source: model | user'))
    op.add_column('sentiment_results',
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True,
                  comment='Last update timestamp'))
    op.add_column('sentiment_results',
        sa.Column('updated_by', sa.UUID(), nullable=True,
                  comment='User ID who made the update'))
    op.add_column('sentiment_results',
        sa.Column('original_sentiment', sa.String(20), nullable=True,
                  comment='Original sentiment before user edit'))
    op.add_column('sentiment_results',
        sa.Column('original_confidence', sa.Float(), nullable=True,
                  comment='Original confidence before user edit'))
    op.add_column('sentiment_results',
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false',
                  comment='Soft delete flag'))
    op.add_column('sentiment_results',
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='User notes for edit reason'))

    # Indexes for sentiment_results
    op.create_index('idx_sentiment_source', 'sentiment_results', ['source'])
    op.create_index('idx_sentiment_updated', 'sentiment_results', ['updated_at'])
    op.create_index('idx_sentiment_deleted', 'sentiment_results', ['is_deleted'])

    # ===== 2. intent_results =====
    op.add_column('intent_results',
        sa.Column('source', sa.String(20), nullable=False, server_default='model',
                  comment='Source: model | user'))
    op.add_column('intent_results',
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True,
                  comment='Last update timestamp'))
    op.add_column('intent_results',
        sa.Column('updated_by', sa.UUID(), nullable=True,
                  comment='User ID who made the update'))
    op.add_column('intent_results',
        sa.Column('original_intent', sa.String(50), nullable=True,
                  comment='Original intent before user edit'))
    op.add_column('intent_results',
        sa.Column('original_confidence', sa.Float(), nullable=True,
                  comment='Original confidence before user edit'))
    op.add_column('intent_results',
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false',
                  comment='Soft delete flag'))
    op.add_column('intent_results',
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='User notes for edit reason'))

    # Indexes for intent_results
    op.create_index('idx_intent_source', 'intent_results', ['source'])
    op.create_index('idx_intent_updated', 'intent_results', ['updated_at'])
    op.create_index('idx_intent_deleted', 'intent_results', ['is_deleted'])

    # ===== 3. aspect_sentiment_results =====
    op.add_column('aspect_sentiment_results',
        sa.Column('source', sa.String(20), nullable=False, server_default='model',
                  comment='Source: model | user'))
    op.add_column('aspect_sentiment_results',
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True,
                  comment='Last update timestamp'))
    op.add_column('aspect_sentiment_results',
        sa.Column('updated_by', sa.UUID(), nullable=True,
                  comment='User ID who made the update'))
    op.add_column('aspect_sentiment_results',
        sa.Column('original_sentiment', sa.String(20), nullable=True,
                  comment='Original sentiment before user edit'))
    op.add_column('aspect_sentiment_results',
        sa.Column('original_confidence', sa.Float(), nullable=True,
                  comment='Original confidence before user edit'))
    op.add_column('aspect_sentiment_results',
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false',
                  comment='Soft delete flag'))
    op.add_column('aspect_sentiment_results',
        sa.Column('notes', sa.Text(), nullable=True,
                  comment='User notes for edit reason'))

    # Indexes for aspect_sentiment_results
    op.create_index('idx_aspect_source', 'aspect_sentiment_results', ['source'])
    op.create_index('idx_aspect_updated', 'aspect_sentiment_results', ['updated_at'])
    op.create_index('idx_aspect_deleted', 'aspect_sentiment_results', ['is_deleted'])


def downgrade() -> None:
    """
    Remove audit trail columns
    """

    # ===== aspect_sentiment_results =====
    op.drop_index('idx_aspect_deleted', table_name='aspect_sentiment_results')
    op.drop_index('idx_aspect_updated', table_name='aspect_sentiment_results')
    op.drop_index('idx_aspect_source', table_name='aspect_sentiment_results')
    op.drop_column('aspect_sentiment_results', 'notes')
    op.drop_column('aspect_sentiment_results', 'is_deleted')
    op.drop_column('aspect_sentiment_results', 'original_confidence')
    op.drop_column('aspect_sentiment_results', 'original_sentiment')
    op.drop_column('aspect_sentiment_results', 'updated_by')
    op.drop_column('aspect_sentiment_results', 'updated_at')
    op.drop_column('aspect_sentiment_results', 'source')

    # ===== intent_results =====
    op.drop_index('idx_intent_deleted', table_name='intent_results')
    op.drop_index('idx_intent_updated', table_name='intent_results')
    op.drop_index('idx_intent_source', table_name='intent_results')
    op.drop_column('intent_results', 'notes')
    op.drop_column('intent_results', 'is_deleted')
    op.drop_column('intent_results', 'original_confidence')
    op.drop_column('intent_results', 'original_intent')
    op.drop_column('intent_results', 'updated_by')
    op.drop_column('intent_results', 'updated_at')
    op.drop_column('intent_results', 'source')

    # ===== sentiment_results =====
    op.drop_index('idx_sentiment_deleted', table_name='sentiment_results')
    op.drop_index('idx_sentiment_updated', table_name='sentiment_results')
    op.drop_index('idx_sentiment_source', table_name='sentiment_results')
    op.drop_column('sentiment_results', 'notes')
    op.drop_column('sentiment_results', 'is_deleted')
    op.drop_column('sentiment_results', 'original_confidence')
    op.drop_column('sentiment_results', 'original_sentiment')
    op.drop_column('sentiment_results', 'updated_by')
    op.drop_column('sentiment_results', 'updated_at')
    op.drop_column('sentiment_results', 'source')
