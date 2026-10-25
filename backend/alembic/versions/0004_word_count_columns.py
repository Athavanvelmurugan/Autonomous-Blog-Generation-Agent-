"""add word count columns to blog_versions and blog_posts

Revision ID: 0004_word_count_columns
Revises: 0003_optimized_indexes
Create Date: 2026-10-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0004_word_count_columns'
down_revision = '0003_optimized_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("ALTER TABLE blog_versions ADD COLUMN IF NOT EXISTS target_word_count INTEGER DEFAULT 800;"))
    bind.execute(text("ALTER TABLE blog_versions ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;"))
    bind.execute(text("ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS target_word_count INTEGER DEFAULT 800;"))
    bind.execute(text("ALTER TABLE blog_posts ADD COLUMN IF NOT EXISTS word_count INTEGER DEFAULT 0;"))


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(text("ALTER TABLE blog_posts DROP COLUMN IF EXISTS word_count;"))
    bind.execute(text("ALTER TABLE blog_posts DROP COLUMN IF EXISTS target_word_count;"))
    bind.execute(text("ALTER TABLE blog_versions DROP COLUMN IF EXISTS word_count;"))
    bind.execute(text("ALTER TABLE blog_versions DROP COLUMN IF EXISTS target_word_count;"))
