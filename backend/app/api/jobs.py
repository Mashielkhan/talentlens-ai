import re
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, func, or_, select

from app.core.security import current_user, require_role
from app.db.session import get_db
from app.models.entities import AuditLog, Job, JobSection, MatchResult
from app.nlp.taxonomy import extract_skills
from app.repositories.access import visible_job
from app.schemas.contracts import JobInput, JobOut, TextInput

router = APIRouter(prefix="/jobs", tags=["Jobs"])
recruiter = require_role("RECRUITER")


@router.post("/suggest")
def suggest(data: TextInput, user=Depends(recruiter)):
    years = re.search(r"(\d{1,2})\+?\s*years?", data.text, re.I)
    return {
        "suggested_skills": extract_skills({"description": data.text}),
        "suggested_experience_months": int(years[1]) * 12 if years else None,
        "notice": "Suggestions only. Classify required/preferred skills and confirm all criteria before publishing.",
    }


@router.post("", response_model=JobOut, status_code=201)
def create(data: JobInput, user=Depends(recruiter), db=Depends(get_db)):
    job = Job(**data.model_dump(), recruiter_id=user.id)
    db.add(job)
    db.flush()
    db.add(AuditLog(actor_id=user.id, action="job.created", resource_id=str(job.id)))
    db.commit()
    return job


@router.get("", response_model=list[JobOut])
def listing(
    q: str = Query("", max_length=200),
    mine: bool = False,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    db=Depends(get_db),
):
    query = (
        select(Job).where(Job.recruiter_id == user.id)
        if mine
        else select(Job).where(Job.status == "PUBLISHED")
    )
    if q.strip():
        terms = func.websearch_to_tsquery("english", q)
        query = query.where(
            or_(
                func.to_tsvector("english", Job.title + " " + Job.description).op("@@")(terms),
                Job.title.ilike("%" + q + "%"),
            )
        )
    return db.scalars(query.order_by(Job.created_at.desc()).limit(limit).offset(offset)).all()


@router.get("/{job_id}", response_model=JobOut)
def detail(job_id: uuid.UUID, user=Depends(current_user), db=Depends(get_db)):
    return visible_job(db, job_id, user)


@router.patch("/{job_id}", response_model=JobOut)
def update(job_id: uuid.UUID, data: JobInput, user=Depends(recruiter), db=Depends(get_db)):
    job = visible_job(db, job_id, user, owner=True, lock=True)
    for key, value in data.model_dump().items():
        setattr(job, key, value)
    job.version += 1
    db.execute(delete(MatchResult).where(MatchResult.job_id == job.id))
    db.execute(delete(JobSection).where(JobSection.job_id == job.id))
    db.add(AuditLog(actor_id=user.id, action="job.updated", resource_id=str(job.id)))
    db.commit()
    return job


@router.delete("/{job_id}", status_code=204)
def remove(job_id: uuid.UUID, user=Depends(recruiter), db=Depends(get_db)):
    job = visible_job(db, job_id, user, owner=True, lock=True)
    db.delete(job)
    db.commit()
