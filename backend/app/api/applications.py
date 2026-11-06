import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import current_user, require_role
from app.db.session import get_db
from app.models.entities import Application, AuditLog, Job, Resume, User
from app.repositories.access import own_resume, visible_job
from app.schemas.contracts import ApplicationInput

router = APIRouter(tags=["Consented applications"])


def application_json(app, db):
    resume, user, job = db.get(Resume, app.resume_id), db.get(User, app.applicant_id), db.get(Job, app.job_id)
    return {
        "id": str(app.id),
        "job_id": str(app.job_id),
        "resume_id": str(app.resume_id),
        "candidate_name": user.full_name,
        "job_title": job.title,
        "company": job.company,
        "status": app.status,
        "resume_status": resume.status,
        "created_at": app.created_at,
        "consent_at": app.consent_at,
    }


@router.post("/jobs/{job_id}/applications", status_code=201)
def apply(
    job_id: uuid.UUID, data: ApplicationInput, user=Depends(require_role("APPLICANT")), db=Depends(get_db)
):
    job = visible_job(db, job_id, user)
    if job.status != "PUBLISHED":
        raise HTTPException(409, "Job is not accepting applications")
    resume = own_resume(db, data.resume_id, user)
    if resume.status != "COMPLETED":
        raise HTTPException(409, "Review your processed resume before applying")
    application = Application(job_id=job_id, applicant_id=user.id, resume_id=resume.id)
    db.add(application)
    try:
        db.flush()
        db.add(
            AuditLog(actor_id=user.id, action="application.consent_granted", resource_id=str(application.id))
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "You have already applied to this job") from exc
    return application_json(application, db)


@router.get("/applications")
def mine(limit: int = Query(100, ge=1, le=100), user=Depends(current_user), db=Depends(get_db)):
    query = (
        select(Application).where(Application.applicant_id == user.id)
        if user.role == "APPLICANT"
        else select(Application).join(Job).where(Job.recruiter_id == user.id)
    )
    return [
        application_json(a, db)
        for a in db.scalars(query.order_by(Application.created_at.desc()).limit(limit))
    ]


@router.get("/jobs/{job_id}/applications")
def for_job(
    job_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=100),
    user=Depends(require_role("RECRUITER")),
    db=Depends(get_db),
):
    visible_job(db, job_id, user, owner=True)
    return [
        application_json(a, db)
        for a in db.scalars(
            select(Application)
            .where(Application.job_id == job_id)
            .order_by(Application.created_at.desc())
            .limit(limit)
        )
    ]


class ApplicationStatus(BaseModel):
    status: Literal["REVIEWED", "SHORTLISTED", "SUBMITTED"]


@router.patch("/applications/{application_id}")
def set_status(
    application_id: uuid.UUID,
    data: ApplicationStatus,
    user=Depends(require_role("RECRUITER")),
    db=Depends(get_db),
):
    app = db.scalar(
        select(Application).join(Job).where(Application.id == application_id, Job.recruiter_id == user.id)
    )
    if not app:
        raise HTTPException(404, "Application not found")
    app.status = data.status
    db.commit()
    return application_json(app, db)


@router.delete("/applications/{application_id}", status_code=204)
def withdraw(application_id: uuid.UUID, user=Depends(require_role("APPLICANT")), db=Depends(get_db)):
    app = db.scalar(
        select(Application)
        .where(Application.id == application_id, Application.applicant_id == user.id)
        .with_for_update()
    )
    if not app:
        raise HTTPException(404, "Application not found")
    db.add(AuditLog(actor_id=user.id, action="application.consent_withdrawn", resource_id=str(app.id)))
    db.delete(app)
    db.commit()
