"""reorder_all_table_columns

Revision ID: 92cb609282f1
Revises: 95d9ca321f39
Create Date: 2026-01-08 20:42:59.303113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '92cb609282f1'
down_revision: Union[str, None] = '95d9ca321f39'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop and recreate all tables with proper column ordering.
    WARNING: This will delete all existing data!
    """

    # Drop all tables with CASCADE to remove foreign key constraints
    op.execute("DROP TABLE IF EXISTS aspect_sentiment_results CASCADE")
    op.execute("DROP TABLE IF EXISTS intent_results CASCADE")
    op.execute("DROP TABLE IF EXISTS sentiment_results CASCADE")
    op.execute("DROP TABLE IF EXISTS feedback_records CASCADE")

    # ========================================
    # Create feedback_records table
    # ========================================
    op.create_table(
        'feedback_records',
        # 1. Primary Key
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),

        # 2-3. Source Information
        sa.Column('source_type', sa.String(length=50), nullable=False, comment='Source type: email, instagram, facebook, google_form, google_maps, manual'),
        sa.Column('source_id', sa.String(length=255), nullable=True, comment='Unique ID from source (e.g., comment_id, email_id)'),

        # 4-6. Content
        sa.Column('text_content', sa.Text(), nullable=False, comment='Main text content of the feedback'),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='Source-specific raw data'),
        sa.Column('created_at_source', postgresql.TIMESTAMP(timezone=True), nullable=True, comment='Original timestamp from source'),

        # 7-8. Processing
        sa.Column('processing_status', sa.String(length=20), nullable=False, server_default='pending', comment='Status: pending, processing, completed, failed'),
        sa.Column('analysis_summary', postgresql.JSONB(astext_type=sa.Text()), nullable=True, comment='ML analysis results summary'),

        # 9-10. Audit Timestamps
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),

        # Primary Key
        sa.PrimaryKeyConstraint('id', name='feedback_records_pkey'),

        # Unique Constraint
        sa.UniqueConstraint('source_type', 'source_id', name='uq_feedback_source')
    )

    # Create indexes for feedback_records
    op.create_index('idx_feedback_source_type', 'feedback_records', ['source_type'])
    op.create_index('idx_feedback_processing_status', 'feedback_records', ['processing_status'])
    op.create_index('idx_feedback_created_at', 'feedback_records', ['created_at'])
    op.create_index('idx_feedback_analysis_summary', 'feedback_records', ['analysis_summary'], postgresql_using='gin')

    # ========================================
    # Create sentiment_results table
    # ========================================
    op.create_table(
        'sentiment_results',
        # 1. Primary Key
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),

        # 2. Foreign Key
        sa.Column('feedback_id', sa.UUID(), nullable=False),

        # 3-4. Core Data
        sa.Column('sentiment', sa.String(length=20), nullable=False, comment='Sentiment: positive, neutral, negative'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Confidence score (0-1)'),

        # 5. Audit Source
        sa.Column('source', sa.String(length=20), nullable=False, server_default='model', comment='Source: model | user'),

        # 6-7. Edit History
        sa.Column('original_sentiment', sa.String(length=20), nullable=True, comment='Original sentiment before user edit'),
        sa.Column('original_confidence', sa.Float(), nullable=True, comment='Original confidence before user edit'),

        # 8-10. Audit Timestamps
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True, comment='User ID who made the update'),

        # 11. Soft Delete
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', comment='Soft delete flag'),

        # 12. Notes
        sa.Column('notes', sa.Text(), nullable=True, comment='User notes for edit reason'),

        # Primary Key
        sa.PrimaryKeyConstraint('id', name='sentiment_results_pkey'),

        # Foreign Key
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback_records.id'], name='sentiment_results_feedback_id_fkey', ondelete='CASCADE')
    )

    # Create indexes for sentiment_results
    op.create_index('idx_sentiment_feedback_id', 'sentiment_results', ['feedback_id'])
    op.create_index('idx_sentiment_sentiment', 'sentiment_results', ['sentiment'])
    op.create_index('idx_sentiment_source', 'sentiment_results', ['source'])
    op.create_index('idx_sentiment_updated', 'sentiment_results', ['updated_at'])
    op.create_index('idx_sentiment_deleted', 'sentiment_results', ['is_deleted'])

    # ========================================
    # Create intent_results table
    # ========================================
    op.create_table(
        'intent_results',
        # 1. Primary Key
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),

        # 2. Foreign Key
        sa.Column('feedback_id', sa.UUID(), nullable=False),

        # 3-4. Core Data
        sa.Column('intent', sa.String(length=50), nullable=False, comment='Intent: feedback, question, complaint, off_topic'),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Confidence score (0-1)'),

        # 5. Audit Source
        sa.Column('source', sa.String(length=20), nullable=False, server_default='model', comment='Source: model | user'),

        # 6-7. Edit History
        sa.Column('original_intent', sa.String(length=50), nullable=True, comment='Original intent before user edit'),
        sa.Column('original_confidence', sa.Float(), nullable=True, comment='Original confidence before user edit'),

        # 8-10. Audit Timestamps
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True, comment='User ID who made the update'),

        # 11. Soft Delete
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', comment='Soft delete flag'),

        # 12. Notes
        sa.Column('notes', sa.Text(), nullable=True, comment='User notes for edit reason'),

        # Primary Key
        sa.PrimaryKeyConstraint('id', name='intent_results_pkey'),

        # Foreign Key
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback_records.id'], name='intent_results_feedback_id_fkey', ondelete='CASCADE')
    )

    # Create indexes for intent_results
    op.create_index('idx_intent_feedback_id', 'intent_results', ['feedback_id'])
    op.create_index('idx_intent_intent', 'intent_results', ['intent'])
    op.create_index('idx_intent_source', 'intent_results', ['source'])
    op.create_index('idx_intent_updated', 'intent_results', ['updated_at'])
    op.create_index('idx_intent_deleted', 'intent_results', ['is_deleted'])

    # ========================================
    # Create aspect_sentiment_results table
    # ========================================
    op.create_table(
        'aspect_sentiment_results',
        # 1. Primary Key
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),

        # 2. Foreign Key
        sa.Column('feedback_id', sa.UUID(), nullable=False),

        # 3-5. Core Data
        sa.Column('aspect', sa.String(length=50), nullable=False, comment='Aspect: equipment, staff, cleanliness, atmosphere, price, location, programs, amenities'),
        sa.Column('sentiment', sa.String(length=20), nullable=False, comment="Sentiment: positive, neutral, negative (note: 'none' not stored in Hybrid++ approach)"),
        sa.Column('confidence', sa.Float(), nullable=True, comment='Confidence score (0-1)'),

        # 6. Audit Source
        sa.Column('source', sa.String(length=20), nullable=False, server_default='model', comment='Source: model | user'),

        # 7-8. Edit History
        sa.Column('original_sentiment', sa.String(length=20), nullable=True, comment='Original sentiment before user edit'),
        sa.Column('original_confidence', sa.Float(), nullable=True, comment='Original confidence before user edit'),

        # 9-11. Audit Timestamps
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('updated_by', sa.UUID(), nullable=True, comment='User ID who made the update'),

        # 12. Soft Delete
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false', comment='Soft delete flag'),

        # 13. Notes
        sa.Column('notes', sa.Text(), nullable=True, comment='User notes for edit reason'),

        # Primary Key
        sa.PrimaryKeyConstraint('id', name='aspect_sentiment_results_pkey'),

        # Foreign Key
        sa.ForeignKeyConstraint(['feedback_id'], ['feedback_records.id'], name='aspect_sentiment_results_feedback_id_fkey', ondelete='CASCADE')
    )

    # Create indexes for aspect_sentiment_results
    op.create_index('idx_aspect_sentiment_feedback_id', 'aspect_sentiment_results', ['feedback_id'])
    op.create_index('idx_aspect_sentiment_aspect', 'aspect_sentiment_results', ['aspect'])
    op.create_index('idx_aspect_sentiment_sentiment', 'aspect_sentiment_results', ['sentiment'])
    op.create_index('idx_aspect_source', 'aspect_sentiment_results', ['source'])
    op.create_index('idx_aspect_updated', 'aspect_sentiment_results', ['updated_at'])
    op.create_index('idx_aspect_deleted', 'aspect_sentiment_results', ['is_deleted'])


def downgrade() -> None:
    """
    Downgrade is not supported for this migration.
    This migration recreates tables with new column order.
    """
    raise NotImplementedError("Downgrade not supported - this migration recreates tables")
