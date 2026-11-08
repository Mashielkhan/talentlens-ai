import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.security import rate_limit, require_role
from app.db.session import get_db
from app.models.entities import CvDraft, User
from app.repositories.access import own_resume
from app.schemas.beta import DraftApprove, DraftCreate, DraftOut, DraftUpdate
from app.services.cv_studio import prepare_draft, render_cv

router = APIRouter(prefix="/studio", tags=["Private CV Studio"])
applicant = require_role("APPLICANT")


def owned(db, draft_id, user, mutable=False):
    draft = db.scalar(select(CvDraft).where(CvDraft.id == draft_id, CvDraft.owner_id == user.id))
    if not draft:
        raise HTTPException(404, "Draft not found")
    source = own_resume(db, draft.resume_id, user, lock=mutable)
    if mutable:
        draft = db.scalar(
            select(CvDraft)
            .where(CvDraft.id == draft_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if source.version != draft.source_version or source.status != "COMPLETED":
            raise HTTPException(409, "Source resume changed. Create a new draft from the processed resume.")
    return draft, source


def output(draft, source):
    result = DraftOut.model_validate(draft)
    result.source_outdated = source.version != draft.source_version or source.status != "COMPLETED"
    return result


@router.post("", response_model=DraftOut, status_code=201)
def create(data: DraftCreate, user=Depends(applicant), db=Depends(get_db)):
    rate_limit("studio-create:" + str(user.id), 15, 3600)
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    if db.scalar(select(func.count()).select_from(CvDraft).where(CvDraft.owner_id == user.id)) >= 30:
        raise HTTPException(409, "Beta limit: delete an old draft before creating another (30 drafts).")
    resume = own_resume(db, data.resume_id, user, lock=True)
    if resume.status != "COMPLETED":
        raise HTTPException(409, "Wait for resume processing before creating a draft")
    try:
        content, guidance = prepare_draft(resume.parsed_data, data.target_description)
    except ValidationError as exc:
        raise HTTPException(
            422, "Some extracted fields are too long for CV Studio. Correct the extraction first."
        ) from exc
    draft = CvDraft(
        owner_id=user.id,
        resume_id=resume.id,
        source_version=resume.version,
        title=data.title.strip(),
        target_description=data.target_description,
        original=content,
        content=content,
        guidance=guidance,
    )
    db.add(draft)
    db.commit()
    return output(draft, resume)


@router.get("", response_model=list[DraftOut])
def list_drafts(user=Depends(applicant), db=Depends(get_db)):
    drafts = db.scalars(
        select(CvDraft).where(CvDraft.owner_id == user.id).order_by(CvDraft.created_at.desc()).limit(30)
    ).all()
    return [output(d, own_resume(db, d.resume_id, user)) for d in drafts]


@router.get("/{draft_id}", response_model=DraftOut)
def detail(draft_id: uuid.UUID, user=Depends(applicant), db=Depends(get_db)):
    return output(*owned(db, draft_id, user))


@router.patch("/{draft_id}", response_model=DraftOut)
def update(draft_id: uuid.UUID, data: DraftUpdate, user=Depends(applicant), db=Depends(get_db)):
    draft, source = owned(db, draft_id, user, mutable=True)
    if data.revision != draft.revision:
        raise HTTPException(409, "This draft changed in another tab. Reload before saving.")
    draft.content = data.content.model_dump()
    draft.revision += 1
    draft.approved_revision = None
    db.commit()
    return output(draft, source)


@router.post("/{draft_id}/approve", response_model=DraftOut)
def approve(draft_id: uuid.UUID, data: DraftApprove, user=Depends(applicant), db=Depends(get_db)):
    draft, source = owned(db, draft_id, user, mutable=True)
    if data.revision != draft.revision:
        raise HTTPException(409, "This draft changed. Review the current revision first.")
    if not draft.content.get("name", "").strip() or not any(
        draft.content.get(k, "").strip() for k in ("experience", "education", "projects")
    ):
        raise HTTPException(422, "Add your name and at least one experience, education or project section")
    draft.approved_revision = draft.revision
    db.commit()
    return output(draft, source)


@router.get("/{draft_id}/export/{kind}")
def export(draft_id: uuid.UUID, kind: Literal["pdf", "docx"], user=Depends(applicant), db=Depends(get_db)):
    rate_limit("studio-export:" + str(user.id), 60, 3600)
    draft, _ = owned(db, draft_id, user, mutable=True)
    if draft.approved_revision != draft.revision:
        raise HTTPException(409, "Review and approve the current draft before exporting")
    mime = (
        "application/pdf"
        if kind == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    try:
        data = render_cv(draft.content, kind)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return Response(
        data,
        media_type=mime,
        headers={
            "Content-Disposition": f'attachment; filename="talentlens-cv.{kind}"',
            "Cache-Control": "no-store",
        },
    )


@router.delete("/{draft_id}", status_code=204)
def remove(draft_id: uuid.UUID, user=Depends(applicant), db=Depends(get_db)):
    draft, _ = owned(db, draft_id, user)
    db.delete(draft)
    db.commit()
