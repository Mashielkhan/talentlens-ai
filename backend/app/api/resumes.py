import hashlib
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile
from sqlalchemy import delete, select

from app.core.config import settings
from app.core.security import current_user, rate_limit, require_role
from app.db.session import get_db
from app.models.entities import AuditLog, Deletion, MatchResult, ProcessingTask, Resume
from app.nlp.documents import DocumentError, validate_file
from app.repositories.access import own_resume, visible_resume
from app.schemas.contracts import Correction, ResumeOut, TaskOut
from app.storage.private import storage

router = APIRouter(prefix="/resumes", tags=["Private resumes"])
applicant = require_role("APPLICANT")


def queue_parse(db, resume, owner):
    task = ProcessingTask(
        owner_id=owner.id, resume_id=resume.id, kind="PARSE", payload={"version": resume.version}
    )
    db.add(task)
    resume.status, resume.stage, resume.error_code = "PENDING", "Queued for processing", None
    db.commit()
    return task


@router.post("", response_model=ResumeOut, status_code=202)
def upload(file: UploadFile, user=Depends(applicant), db=Depends(get_db)):
    rate_limit("upload:" + str(user.id), 15, 3600)
    data = file.file.read(settings().max_upload_bytes + 1)
    try:
        suffix = validate_file(data, file.filename or "", file.content_type or "")
    except DocumentError as exc:
        raise HTTPException(422, str(exc)) from exc
    resume = Resume(
        id=uuid.uuid4(),
        owner_id=user.id,
        original_filename=Path((file.filename or "resume").replace("\\", "/")).name[:255],
        storage_key=f"{uuid.uuid4()}{suffix}",
        mime_type=file.content_type,
        file_size=len(data),
        file_hash=hashlib.sha256(data).hexdigest(),
        version=1,
    )
    storage().put(resume.storage_key, data)
    try:
        db.add(resume)
        db.flush()
        db.add(AuditLog(actor_id=user.id, action="resume.uploaded", resource_id=str(resume.id)))
        queue_parse(db, resume, user)
    except Exception:
        db.rollback()
        storage().delete(resume.storage_key)
        raise
    return resume


@router.get("", response_model=list[ResumeOut])
def list_resumes(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user=Depends(current_user),
    db=Depends(get_db),
):
    return db.scalars(
        select(Resume)
        .where(Resume.owner_id == user.id)
        .order_by(Resume.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()


@router.get("/{resume_id}", response_model=ResumeOut)
def detail(resume_id: uuid.UUID, user=Depends(current_user), db=Depends(get_db)):
    return visible_resume(db, resume_id, user)


@router.get("/{resume_id}/download")
def download(resume_id: uuid.UUID, user=Depends(current_user), db=Depends(get_db)):
    resume = visible_resume(db, resume_id, user)
    data = storage().read(resume.storage_key)
    suffix = resume.storage_key.rsplit(".", 1)[1]
    return Response(
        data,
        media_type=resume.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="resume.{suffix}"',
            "Cache-Control": "no-store",
        },
    )


@router.patch("/{resume_id}", response_model=TaskOut, status_code=202)
def correct(resume_id: uuid.UUID, data: Correction, user=Depends(applicant), db=Depends(get_db)):
    resume = own_resume(db, resume_id, user, lock=True)
    resume.corrections = data.model_dump()
    resume.version += 1
    db.execute(delete(MatchResult).where(MatchResult.resume_id == resume.id))
    db.add(AuditLog(actor_id=user.id, action="resume.corrected", resource_id=str(resume.id)))
    return queue_parse(db, resume, user)


@router.post("/{resume_id}/reprocess", response_model=TaskOut, status_code=202)
def reprocess(resume_id: uuid.UUID, user=Depends(applicant), db=Depends(get_db)):
    rate_limit("reprocess:" + str(user.id), 15, 3600)
    resume = own_resume(db, resume_id, user, lock=True)
    if resume.status in {"PENDING", "PROCESSING", "RETRYING"}:
        raise HTTPException(409, "Resume processing is already queued")
    resume.version += 1
    db.execute(delete(MatchResult).where(MatchResult.resume_id == resume.id))
    return queue_parse(db, resume, user)


@router.delete("/{resume_id}", status_code=204)
def remove(resume_id: uuid.UUID, user=Depends(applicant), db=Depends(get_db)):
    resume = own_resume(db, resume_id, user, lock=True)
    db.add(Deletion(storage_key=resume.storage_key))
    db.add(AuditLog(actor_id=user.id, action="resume.deleted", resource_id=str(resume.id)))
    db.delete(resume)
    db.commit()
