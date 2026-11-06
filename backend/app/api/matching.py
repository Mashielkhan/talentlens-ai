import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.core.security import current_user, rate_limit, require_role
from app.db.session import get_db
from app.models.entities import Application, Job, MatchResult, ProcessingTask, Resume, User
from app.repositories.access import own_resume, visible_job, visible_match
from app.schemas.contracts import AnalysisInput, TaskOut

router = APIRouter(tags=["Matching"])


def enqueue(db, user, job, kind, resume=None):
    rate_limit("match:" + str(user.id), 30, 3600)
    if not job.requirements_confirmed:
        raise HTTPException(409, "Job requirements must be confirmed")
    existing = select(ProcessingTask).where(
        ProcessingTask.owner_id == user.id,
        ProcessingTask.job_id == job.id,
        ProcessingTask.kind == kind,
        ProcessingTask.status.in_(["PENDING", "PROCESSING", "RETRYING"]),
    )
    if resume:
        existing = existing.where(ProcessingTask.resume_id == resume.id)
    task = db.scalar(existing)
    if task:
        return task
    task = ProcessingTask(
        owner_id=user.id,
        job_id=job.id,
        resume_id=resume.id if resume else None,
        kind=kind,
        payload={"job_version": job.version},
    )
    db.add(task)
    db.commit()
    return task


def match_json(match, db):
    resume = db.get(Resume, match.resume_id)
    owner = db.get(User, resume.owner_id)
    return {
        "id": str(match.id),
        "job_id": str(match.job_id),
        "resume_id": str(match.resume_id),
        "application_id": str(match.application_id) if match.application_id else None,
        "candidate_name": owner.full_name,
        "created_at": match.created_at,
        **match.result,
    }


@router.post("/skill-gap/analyze", response_model=TaskOut, status_code=202)
def analyze(data: AnalysisInput, user=Depends(require_role("APPLICANT")), db=Depends(get_db)):
    job, resume = visible_job(db, data.job_id, user), own_resume(db, data.resume_id, user)
    if resume.status != "COMPLETED":
        raise HTTPException(409, "Resume is not ready for analysis")
    return enqueue(db, user, job, "ANALYZE", resume)


@router.post("/jobs/{job_id}/match", response_model=TaskOut, status_code=202)
def rank(job_id: uuid.UUID, user=Depends(require_role("RECRUITER")), db=Depends(get_db)):
    job = visible_job(db, job_id, user, owner=True)
    return enqueue(db, user, job, "MATCH_JOB")


@router.get("/tasks/{task_id}", response_model=TaskOut)
def task_state(task_id: uuid.UUID, user=Depends(current_user), db=Depends(get_db)):
    task = db.scalar(
        select(ProcessingTask).where(ProcessingTask.id == task_id, ProcessingTask.owner_id == user.id)
    )
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.get("/matches")
def matches(
    job_id: uuid.UUID | None = None,
    limit: int = Query(100, ge=1, le=100),
    user=Depends(current_user),
    db=Depends(get_db),
):
    query = (
        select(MatchResult)
        .join(Resume)
        .join(Job, Job.id == MatchResult.job_id)
        .where(MatchResult.job_version == Job.version, MatchResult.resume_version == Resume.version)
    )
    if user.role == "APPLICANT":
        query = query.where(Resume.owner_id == user.id)
    else:
        query = query.join(Application, Application.id == MatchResult.application_id).where(
            Job.recruiter_id == user.id
        )
    if job_id:
        query = query.where(Job.id == job_id)
    return [match_json(m, db) for m in db.scalars(query.order_by(MatchResult.score.desc()).limit(limit))]


@router.get("/matches/{match_id}")
def detail(match_id: uuid.UUID, user=Depends(current_user), db=Depends(get_db)):
    return match_json(visible_match(db, match_id, user), db)
