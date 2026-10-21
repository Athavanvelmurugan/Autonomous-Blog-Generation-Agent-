"""baseline blog_posts table

Revision ID: 0001_baseline
Revises: 
Create Date: 2026-10-20 23:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '0001_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    if 'blog_posts' not in tables:
        op.create_table(
            'blog_posts',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('topic', sa.String(length=300), nullable=False),
            sa.Column('tone', sa.String(length=50), nullable=False),
            sa.Column('target_language', sa.String(length=50), nullable=False),
            sa.Column('title', sa.Text(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('verification_score', sa.Float(), nullable=True),
            sa.Column('critique', sa.Text(), nullable=True),
            sa.Column('sources_json', sa.Text(), nullable=True),
            sa.Column('original_title', sa.Text(), nullable=True),
            sa.Column('original_content', sa.Text(), nullable=True),
            sa.Column('execution_time_seconds', sa.Float(), nullable=True),
            sa.Column('steps_completed_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_blog_posts_id'), 'blog_posts', ['id'], unique=False)
        op.create_index(op.f('ix_blog_posts_topic'), 'blog_posts', ['topic'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_blog_posts_topic'), table_name='blog_posts')
    op.drop_index(op.f('ix_blog_posts_id'), table_name='blog_posts')
    op.drop_table('blog_posts')
