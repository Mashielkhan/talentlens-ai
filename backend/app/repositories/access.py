from fastapi import HTTPException
from sqlalchemy import select

from app.models.entities import Application, Job, MatchResult, Resume


def own_resume(db, resume_id, user, lock=False):
    query = select(Resume).where(Resume.id == resume_id, Resume.owner_id == user.id)
    resume = db.scalar(query.with_for_update() if lock else query)
    if not resume:
        raise HTTPException(404, "Resume not found")
    return resume


def visible_resume(db, resume_id, user):
    resume = db.get(Resume, resume_id)
    if resume and resume.owner_id == user.id:
        return resume
    consent = db.scalar(
        select(Application.id)
        .join(Job)
        .where(Application.resume_id == resume_id, Job.recruiter_id == user.id)
    )
    if not resume or not consent:
        raise HTTPException(404, "Resume not found")
    return resume


def visible_job(db, job_id, user, owner=False, lock=False):
    query = select(Job).where(Job.id == job_id)
    job = db.scalar(query.with_for_update() if lock else query)
    if (
        not job
        or (owner and job.recruiter_id != user.id)
        or (job.status != "PUBLISHED" and job.recruiter_id != user.id)
    ):
        raise HTTPException(404, "Job not found")
    return job


def visible_match(db, match_id, user):
    match = db.get(MatchResult, match_id)
    if not match:
        raise HTTPException(404, "Analysis not found")
    resume, job = db.get(Resume, match.resume_id), db.get(Job, match.job_id)
    allowed = resume.owner_id == user.id
    if match.application_id and job.recruiter_id == user.id:
        allowed = db.get(Application, match.application_id) is not None
    if not allowed:
        raise HTTPException(404, "Analysis not found")
    if match.resume_version != resume.version or match.job_version != job.version:
        raise HTTPException(409, "This analysis is outdated; run matching again")
    return match
