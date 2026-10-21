"""composite and partial indexes for 100x query optimization

Revision ID: 0003_optimized_indexes
Revises: 0002_normalized
Create Date: 2026-10-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_optimized_indexes'
down_revision = '0002_normalized'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Partial index on active blogs ordered by created_at DESC (eliminates sorting for keyset pagination)
    op.create_index(
        'ix_blogs_active_created',
        'blogs',
        [sa.text('created_at DESC')],
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    # 2. Multi-column partial index for user-filtered keyset pagination
    op.create_index(
        'ix_blogs_user_active_created',
        'blogs',
        ['user_id', sa.text('created_at DESC')],
        postgresql_where=sa.text('deleted_at IS NULL')
    )

    # 3. Composite index on blog_versions for instant latest-version lookup
    op.create_index(
        'ix_blog_versions_blog_ver',
        'blog_versions',
        ['blog_id', sa.text('version_number DESC')]
    )

    # 4. Composite index on run_steps for ordered step retrieval
    op.create_index(
        'ix_run_steps_run_order',
        'run_steps',
        ['run_id', sa.text('step_order ASC')]
    )

    # 5. Composite index on llm_calls for chronological metrics breakdown
    op.create_index(
        'ix_llm_calls_run_created',
        'llm_calls',
        ['run_id', sa.text('created_at ASC')]
    )

    # 6. Composite index on agent_runs for blog run history
    op.create_index(
        'ix_agent_runs_blog_created',
        'agent_runs',
        ['blog_id', sa.text('created_at DESC')]
    )

    # 7. Analytics composite index on reader_events
    op.create_index(
        'ix_reader_events_blog_type',
        'reader_events',
        ['blog_id', 'event_type', sa.text('created_at DESC')]
    )


def downgrade() -> None:
    op.drop_index('ix_reader_events_blog_type', table_name='reader_events')
    op.drop_index('ix_agent_runs_blog_created', table_name='agent_runs')
    op.drop_index('ix_llm_calls_run_created', table_name='llm_calls')
    op.drop_index('ix_run_steps_run_order', table_name='run_steps')
    op.drop_index('ix_blog_versions_blog_ver', table_name='blog_versions')
    op.drop_index('ix_blogs_user_active_created', table_name='blogs')
    op.drop_index('ix_blogs_active_created', table_name='blogs')
