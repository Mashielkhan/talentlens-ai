"""Private CV drafts, account recovery and beta feedback."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def identity():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def owner():
    return sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)


def upgrade():
    op.create_table(
        "cv_drafts",
        *identity(),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resume_id", sa.Uuid(), sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("target_description", sa.Text(), nullable=False),
        sa.Column("original", JSONB(), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("guidance", JSONB(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("approved_revision", sa.Integer(), nullable=True),
    )
    op.create_index("ix_cv_drafts_owner_id", "cv_drafts", ["owner_id"])
    op.create_index("ix_cv_drafts_resume_id", "cv_drafts", ["resume_id"])
    op.create_table(
        "account_tokens",
        *identity(),
        owner(),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_tokens_user_id", "account_tokens", ["user_id"])
    op.create_table(
        "beta_feedback",
        *identity(),
        owner(),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
    )
    op.create_index("ix_beta_feedback_user_id", "beta_feedback", ["user_id"])


def downgrade():
    op.drop_table("beta_feedback")
    op.drop_table("account_tokens")
    op.drop_table("cv_drafts")
