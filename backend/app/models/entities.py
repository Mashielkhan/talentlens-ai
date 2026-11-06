import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")
VectorType = Vector(384).with_variant(JSON(), "sqlite")


def now():
    return datetime.now(UTC)


class Identity:
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class User(Identity, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(254), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    profile: Mapped[dict] = mapped_column(JSONType, default=dict)
    __table_args__ = (CheckConstraint("role IN ('APPLICANT','RECRUITER','ADMIN')"),)


class Session(Identity, Base):
    __tablename__ = "sessions"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    csrf_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Resume(Identity, Base):
    __tablename__ = "resumes"
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
    mime_type: Mapped[str] = mapped_column(String(120))
    file_size: Mapped[int] = mapped_column(Integer)
    file_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    stage: Mapped[str] = mapped_column(String(80), default="Queued")
    error_code: Mapped[str | None] = mapped_column(String(80))
    raw_text: Mapped[str | None] = mapped_column(Text)
    parsed_data: Mapped[dict] = mapped_column(JSONType, default=dict)
    corrections: Mapped[dict] = mapped_column(JSONType, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parser_version: Mapped[str] = mapped_column(String(40), default="rules-spacy-1.0")
    model_version: Mapped[str | None] = mapped_column(String(255))


class ResumeSection(Identity, Base):
    __tablename__ = "resume_sections"
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    section_type: Mapped[str] = mapped_column(String(30))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(VectorType)
    model_version: Mapped[str] = mapped_column(String(255))


class Job(Identity, Base):
    __tablename__ = "jobs"
    recruiter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(160))
    company: Mapped[str] = mapped_column(String(160))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(160), default="Remote")
    employment_type: Mapped[str] = mapped_column(String(40), default="Full-time")
    remote_policy: Mapped[str] = mapped_column(String(30), default="Remote")
    status: Mapped[str] = mapped_column(String(16), default="DRAFT")
    required_skills: Mapped[list] = mapped_column(JSONType, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSONType, default=list)
    min_experience_months: Mapped[int] = mapped_column(Integer, default=0)
    education_requirement: Mapped[str] = mapped_column(String(255), default="")
    requirements_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')"),
        Index("ix_jobs_status", "status"),
    )


class JobSection(Identity, Base):
    __tablename__ = "job_sections"
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(VectorType)
    model_version: Mapped[str] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer)


class Application(Identity, Base):
    __tablename__ = "applications"
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    applicant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    consent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    status: Mapped[str] = mapped_column(String(20), default="SUBMITTED")
    __table_args__ = (UniqueConstraint("job_id", "applicant_id"),)


class MatchResult(Identity, Base):
    __tablename__ = "match_results"
    job_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), index=True
    )
    job_version: Mapped[int] = mapped_column(Integer)
    resume_version: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    result: Mapped[dict] = mapped_column(JSONType)
    model_version: Mapped[str] = mapped_column(String(255))
    scoring_version: Mapped[str] = mapped_column(String(80))


class ProcessingTask(Identity, Base):
    __tablename__ = "processing_tasks"
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("jobs.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    error_code: Mapped[str | None] = mapped_column(String(80))
    payload: Mapped[dict] = mapped_column(JSONType, default=dict)
    result: Mapped[dict] = mapped_column(JSONType, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditLog(Identity, Base):
    __tablename__ = "audit_logs"
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    action: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str] = mapped_column(String(80))


class Deletion(Identity, Base):
    """Durable storage deletion outbox; survives account and resume deletion."""

    __tablename__ = "storage_deletions"
    storage_key: Mapped[str] = mapped_column(String(255), unique=True)
