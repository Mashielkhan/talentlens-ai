import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.security import current_user
from app.db.session import get_db
from app.repositories.access import visible_match
from app.services.reports import render_report

router = APIRouter(prefix="/reports", tags=["Private PDF exports"])


@router.get("/compare")
def compare(
    ids: list[uuid.UUID] = Query(min_length=2, max_length=4), user=Depends(current_user), db=Depends(get_db)
):
    matches = [visible_match(db, match_id, user) for match_id in ids]
    if len({m.job_id for m in matches}) != 1:
        raise HTTPException(422, "Compare candidates for the same job")
    return Response(
        render_report([m.result for m in matches], "Candidate qualification comparison"),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="talentlens-comparison.pdf"'},
    )


@router.get("/{match_id}/export")
def export(match_id: uuid.UUID, user=Depends(current_user), db=Depends(get_db)):
    match = visible_match(db, match_id, user)
    return Response(
        render_report([match.result]),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="talentlens-analysis.pdf"'},
    )
