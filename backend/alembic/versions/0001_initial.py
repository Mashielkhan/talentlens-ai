"""Initial schema. Fixed migration snapshot; independent of live ORM models."""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def identity():
    return [
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    ]


def fk(name, table, nullable=False, ondelete="CASCADE"):
    return sa.Column(name, sa.Uuid(), sa.ForeignKey(table + ".id", ondelete=ondelete), nullable=nullable)


def column(name, kind, nullable=False, **kwargs):
    return sa.Column(name, kind, nullable=nullable, **kwargs)


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "users",
        *identity(),
        column("email", sa.String(254), unique=True),
        column("full_name", sa.String(120)),
        column("password_hash", sa.String(255)),
        column("role", sa.String(16)),
        column("is_active", sa.Boolean()),
        column("email_verified", sa.Boolean()),
        column("profile", JSONB()),
        sa.CheckConstraint("role IN ('APPLICANT','RECRUITER','ADMIN')"),
    )
    op.create_table(
        "sessions",
        *identity(),
        fk("user_id", "users"),
        column("token_hash", sa.String(64), unique=True),
        column("csrf_hash", sa.String(64)),
        column("expires_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "resumes",
        *identity(),
        fk("owner_id", "users"),
        column("original_filename", sa.String(255)),
        column("storage_key", sa.String(255), unique=True),
        column("mime_type", sa.String(120)),
        column("file_size", sa.Integer()),
        column("file_hash", sa.String(64)),
        column("status", sa.String(20)),
        column("stage", sa.String(80)),
        column("error_code", sa.String(80), True),
        column("raw_text", sa.Text(), True),
        column("parsed_data", JSONB()),
        column("corrections", JSONB()),
        column("version", sa.Integer()),
        column("parser_version", sa.String(40)),
        column("model_version", sa.String(255), True),
    )
    op.create_table(
        "resume_sections",
        *identity(),
        fk("resume_id", "resumes"),
        column("section_type", sa.String(30)),
        column("text", sa.Text()),
        column("embedding", Vector(384)),
        column("model_version", sa.String(255)),
    )
    op.create_table(
        "jobs",
        *identity(),
        fk("recruiter_id", "users"),
        column("title", sa.String(160)),
        column("company", sa.String(160)),
        column("description", sa.Text()),
        column("location", sa.String(160)),
        column("employment_type", sa.String(40)),
        column("remote_policy", sa.String(30)),
        column("status", sa.String(16)),
        column("required_skills", JSONB()),
        column("preferred_skills", JSONB()),
        column("min_experience_months", sa.Integer()),
        column("education_requirement", sa.String(255)),
        column("requirements_confirmed", sa.Boolean()),
        column("version", sa.Integer()),
        sa.CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')"),
    )
    op.create_table(
        "job_sections",
        *identity(),
        fk("job_id", "jobs"),
        column("text", sa.Text()),
        column("embedding", Vector(384)),
        column("model_version", sa.String(255)),
        column("version", sa.Integer()),
    )
    op.create_table(
        "applications",
        *identity(),
        fk("job_id", "jobs"),
        fk("applicant_id", "users"),
        fk("resume_id", "resumes"),
        column("consent_at", sa.DateTime(timezone=True)),
        column("status", sa.String(20)),
        sa.UniqueConstraint("job_id", "applicant_id"),
    )
    op.create_table(
        "match_results",
        *identity(),
        fk("job_id", "jobs"),
        fk("resume_id", "resumes"),
        fk("requester_id", "users"),
        fk("application_id", "applications", True),
        column("job_version", sa.Integer()),
        column("resume_version", sa.Integer()),
        column("score", sa.Float()),
        column("result", JSONB()),
        column("model_version", sa.String(255)),
        column("scoring_version", sa.String(80)),
    )
    op.create_table(
        "processing_tasks",
        *identity(),
        fk("owner_id", "users"),
        fk("resume_id", "resumes", True),
        fk("job_id", "jobs", True),
        column("kind", sa.String(30)),
        column("status", sa.String(20)),
        column("progress", sa.Integer()),
        column("attempts", sa.Integer()),
        column("error_code", sa.String(80), True),
        column("payload", JSONB()),
        column("result", JSONB()),
        column("started_at", sa.DateTime(timezone=True), True),
        column("completed_at", sa.DateTime(timezone=True), True),
    )
    op.create_table(
        "audit_logs",
        *identity(),
        fk("actor_id", "users", True, "SET NULL"),
        column("action", sa.String(80)),
        column("resource_id", sa.String(80)),
    )
    op.create_table("storage_deletions", *identity(), column("storage_key", sa.String(255), unique=True))
    indexes = {
        "sessions": ["user_id"],
        "resumes": ["owner_id", "file_hash"],
        "resume_sections": ["resume_id"],
        "jobs": ["recruiter_id", "status"],
        "job_sections": ["job_id"],
        "applications": ["job_id", "applicant_id", "resume_id"],
        "match_results": ["job_id", "resume_id", "requester_id", "application_id"],
        "processing_tasks": ["owner_id", "resume_id", "job_id", "status"],
        "audit_logs": ["actor_id"],
    }
    for table, columns in indexes.items():
        for name in columns:
            op.create_index(f"ix_{table}_{name}", table, [name])
    op.execute(
        "CREATE INDEX ix_jobs_fts ON jobs USING gin (to_tsvector('english', title || ' ' || description))"
    )


def downgrade():
    for table in [
        "storage_deletions",
        "audit_logs",
        "processing_tasks",
        "match_results",
        "applications",
        "job_sections",
        "jobs",
        "resume_sections",
        "resumes",
        "sessions",
        "users",
    ]:
        op.drop_table(table)
