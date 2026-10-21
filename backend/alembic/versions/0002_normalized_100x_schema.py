"""normalized 100x schema

Revision ID: 0002_normalized
Revises: 0001_baseline
Create Date: 2026-10-20 23:56:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_normalized'
down_revision = '0001_baseline'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. api_keys
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(length=128), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False, server_default='default'),
        sa.Column('revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)

    # 3. blogs
    op.create_table(
        'blogs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uuid', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('topic', sa.String(length=300), nullable=False),
        sa.Column('tone', sa.String(length=50), nullable=False, server_default='Informative'),
        sa.Column('target_language', sa.String(length=50), nullable=False, server_default='English'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='published'),
        sa.Column('current_version_id', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blogs_id'), 'blogs', ['id'], unique=False)
    op.create_index(op.f('ix_blogs_uuid'), 'blogs', ['uuid'], unique=True)
    op.create_index(op.f('ix_blogs_user_id'), 'blogs', ['user_id'], unique=False)
    op.create_index(op.f('ix_blogs_topic'), 'blogs', ['topic'], unique=False)
    op.create_index(op.f('ix_blogs_status'), 'blogs', ['status'], unique=False)
    op.create_index(op.f('ix_blogs_deleted_at'), 'blogs', ['deleted_at'], unique=False)
    op.create_index(op.f('ix_blogs_created_at'), 'blogs', ['created_at'], unique=False)

    # 4. blog_versions
    op.create_table(
        'blog_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('blog_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('original_title', sa.Text(), nullable=True),
        sa.Column('original_content', sa.Text(), nullable=True),
        sa.Column('verification_score', sa.Float(), nullable=True, server_default='8.5'),
        sa.Column('critique', sa.Text(), nullable=True),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('steps_completed_json', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_blog_versions_id'), 'blog_versions', ['id'], unique=False)
    op.create_index(op.f('ix_blog_versions_blog_id'), 'blog_versions', ['blog_id'], unique=False)
    op.create_index(op.f('ix_blog_versions_created_at'), 'blog_versions', ['created_at'], unique=False)

    # 5. agent_runs
    op.create_table(
        'agent_runs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('idempotency_key', sa.String(length=128), nullable=False),
        sa.Column('blog_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('thread_id', sa.String(length=128), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('total_execution_time_seconds', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_runs_id'), 'agent_runs', ['id'], unique=False)
    op.create_index(op.f('ix_agent_runs_idempotency_key'), 'agent_runs', ['idempotency_key'], unique=True)
    op.create_index(op.f('ix_agent_runs_blog_id'), 'agent_runs', ['blog_id'], unique=False)
    op.create_index(op.f('ix_agent_runs_user_id'), 'agent_runs', ['user_id'], unique=False)
    op.create_index(op.f('ix_agent_runs_thread_id'), 'agent_runs', ['thread_id'], unique=False)
    op.create_index(op.f('ix_agent_runs_status'), 'agent_runs', ['status'], unique=False)
    op.create_index(op.f('ix_agent_runs_created_at'), 'agent_runs', ['created_at'], unique=False)

    # 6. run_steps
    op.create_table(
        'run_steps',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=False),
        sa.Column('node_name', sa.String(length=100), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='completed'),
        sa.Column('input_state_json', sa.Text(), nullable=True),
        sa.Column('output_state_json', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_run_steps_id'), 'run_steps', ['id'], unique=False)
    op.create_index(op.f('ix_run_steps_run_id'), 'run_steps', ['run_id'], unique=False)
    op.create_index(op.f('ix_run_steps_node_name'), 'run_steps', ['node_name'], unique=False)

    # 7. llm_calls
    op.create_table(
        'llm_calls',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('step_id', sa.Integer(), nullable=True),
        sa.Column('node_name', sa.String(length=100), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('total_tokens', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('cost_usd', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('latency_seconds', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['step_id'], ['run_steps.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_calls_id'), 'llm_calls', ['id'], unique=False)
    op.create_index(op.f('ix_llm_calls_run_id'), 'llm_calls', ['run_id'], unique=False)
    op.create_index(op.f('ix_llm_calls_step_id'), 'llm_calls', ['step_id'], unique=False)
    op.create_index(op.f('ix_llm_calls_node_name'), 'llm_calls', ['node_name'], unique=False)
    op.create_index(op.f('ix_llm_calls_created_at'), 'llm_calls', ['created_at'], unique=False)

    # 8. sources
    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('blog_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index(op.f('ix_sources_run_id'), 'sources', ['run_id'], unique=False)
    op.create_index(op.f('ix_sources_blog_id'), 'sources', ['blog_id'], unique=False)
    op.create_index(op.f('ix_sources_domain'), 'sources', ['domain'], unique=False)

    # 9. fact_checks
    op.create_table(
        'fact_checks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('run_id', sa.String(length=36), nullable=True),
        sa.Column('blog_version_id', sa.Integer(), nullable=True),
        sa.Column('score', sa.Float(), nullable=False, server_default='8.5'),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('critique', sa.Text(), nullable=True),
        sa.Column('hallucinations_json', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('unverified_commands_json', sa.Text(), nullable=True, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['blog_version_id'], ['blog_versions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['run_id'], ['agent_runs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_fact_checks_id'), 'fact_checks', ['id'], unique=False)
    op.create_index(op.f('ix_fact_checks_run_id'), 'fact_checks', ['run_id'], unique=False)
    op.create_index(op.f('ix_fact_checks_blog_version_id'), 'fact_checks', ['blog_version_id'], unique=False)

    # 10. claims
    op.create_table(
        'claims',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fact_check_id', sa.Integer(), nullable=False),
        sa.Column('claim_text', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='verified'),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('evidence', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['fact_check_id'], ['fact_checks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_claims_id'), 'claims', ['id'], unique=False)
    op.create_index(op.f('ix_claims_fact_check_id'), 'claims', ['fact_check_id'], unique=False)
    op.create_index(op.f('ix_claims_source_id'), 'claims', ['source_id'], unique=False)

    # 11. prompt_versions
    op.create_table(
        'prompt_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('prompt_name', sa.String(length=100), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('template_text', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_prompt_versions_id'), 'prompt_versions', ['id'], unique=False)
    op.create_index(op.f('ix_prompt_versions_prompt_name'), 'prompt_versions', ['prompt_name'], unique=False)

    # 12. reader_events
    op.create_table(
        'reader_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('blog_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True, server_default='{}'),
        sa.Column('ip_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['blog_id'], ['blogs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reader_events_id'), 'reader_events', ['id'], unique=False)
    op.create_index(op.f('ix_reader_events_blog_id'), 'reader_events', ['blog_id'], unique=False)
    op.create_index(op.f('ix_reader_events_event_type'), 'reader_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_reader_events_created_at'), 'reader_events', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop in reverse order to respect foreign key constraints
    op.drop_table('reader_events')
    op.drop_table('prompt_versions')
    op.drop_table('claims')
    op.drop_table('fact_checks')
    op.drop_table('sources')
    op.drop_table('llm_calls')
    op.drop_table('run_steps')
    op.drop_table('agent_runs')
    op.drop_table('blog_versions')
    op.drop_table('blogs')
    op.drop_table('api_keys')
    op.drop_table('users')
