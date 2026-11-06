import logging
import uuid
from datetime import UTC, datetime, timedelta

from celery import Celery
from sqlalchemy import or_, select, text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.models.entities import Deletion, ProcessingTask, Resume
from app.nlp.documents import DocumentError
from app.services.processing import process_resume, run_matching
from app.storage.private import storage

logger = logging.getLogger(__name__)
celery = Celery("talentlens", broker=settings().redis_url)
celery.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=540,
    task_time_limit=600,
    broker_connection_retry_on_startup=True,
    beat_schedule={"dispatch-outbox": {"task": "dispatch", "schedule": 10.0}},
)


@celery.task(name="dispatch")
def dispatch():
    with SessionLocal() as db:
        cutoff = datetime.now(UTC) - timedelta(minutes=12)
        tasks = db.scalars(
            select(ProcessingTask)
            .where(
                or_(
                    ProcessingTask.status.in_(["PENDING", "RETRYING"]),
                    (ProcessingTask.status == "PROCESSING") & (ProcessingTask.started_at < cutoff),
                )
            )
            .limit(100)
        ).all()
        for task in tasks:
            execute.delay(str(task.id))
        for item in db.scalars(select(Deletion).limit(100)):
            storage().delete(item.storage_key)
            db.delete(item)
        db.commit()


@celery.task(name="execute")
def execute(task_id):
    # Session-level PostgreSQL advisory lock prevents duplicate deliveries from doing work.
    lock_id = uuid.UUID(task_id).int % (2**63 - 1)
    with engine.connect() as connection:
        if not connection.scalar(text("SELECT pg_try_advisory_lock(:id)"), {"id": lock_id}):
            return
        try:
            _execute(uuid.UUID(task_id))
        finally:
            connection.execute(text("SELECT pg_advisory_unlock(:id)"), {"id": lock_id})


def _execute(task_id):
    with SessionLocal() as db:
        task = db.get(ProcessingTask, task_id)
        if not task or task.status in {"COMPLETED", "FAILED"}:
            return
        task.status, task.progress, task.started_at = "PROCESSING", 15, datetime.now(UTC)
        task.attempts += 1
        if task.kind == "PARSE":
            resume = db.get(Resume, task.resume_id)
            if resume and resume.version == task.payload["version"]:
                resume.status, resume.stage = "PROCESSING", "Extracting qualifications and embedding sections"
        db.commit()
        try:
            result = process_resume(db, task) if task.kind == "PARSE" else run_matching(db, task)
            task.result, task.status, task.progress = result, "COMPLETED", 100
            task.completed_at = datetime.now(UTC)
            db.commit()
        except Exception as exc:
            db.rollback()
            task = db.get(ProcessingTask, task_id)
            if not task:
                return
            permanent = isinstance(exc, (DocumentError, ValueError))
            task.status = "FAILED" if permanent or task.attempts >= 3 else "RETRYING"
            task.error_code = str(exc)[:80] if permanent else "PROCESSING_DEPENDENCY_ERROR"
            if task.kind == "PARSE":
                resume = db.get(Resume, task.resume_id)
                if resume and resume.version == task.payload["version"]:
                    resume.status, resume.error_code = task.status, task.error_code
                    resume.stage = "Processing failed; inspect error and retry"
            db.commit()
            # Do not log resume text, exception bodies, credentials, or contact information.
            logger.error("task_failed", extra={"task_id": str(task_id), "error_type": type(exc).__name__})
