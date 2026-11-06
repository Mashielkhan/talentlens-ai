from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.security import current_user
from app.db.session import get_db
from app.models.entities import Application, Job, MatchResult, Resume

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("")
def analytics(user=Depends(current_user), db=Depends(get_db)):
    if user.role == "APPLICANT":
        resumes = db.scalars(select(Resume).where(Resume.owner_id == user.id)).all()
        applications = db.scalars(select(Application).where(Application.applicant_id == user.id)).all()
        jobs = []
        matches = db.scalars(
            select(MatchResult)
            .join(Resume)
            .join(Job, Job.id == MatchResult.job_id)
            .where(
                Resume.owner_id == user.id,
                MatchResult.resume_version == Resume.version,
                MatchResult.job_version == Job.version,
            )
        ).all()
    else:
        jobs = db.scalars(select(Job).where(Job.recruiter_id == user.id)).all()
        applications = db.scalars(select(Application).join(Job).where(Job.recruiter_id == user.id)).all()
        resumes = db.scalars(
            select(Resume).join(Application).join(Job).where(Job.recruiter_id == user.id).distinct()
        ).all()
        matches = db.scalars(
            select(MatchResult)
            .join(Application, Application.id == MatchResult.application_id)
            .join(Job, Job.id == MatchResult.job_id)
            .join(Resume, Resume.id == MatchResult.resume_id)
            .where(
                Job.recruiter_id == user.id,
                MatchResult.resume_version == Resume.version,
                MatchResult.job_version == Job.version,
            )
        ).all()
    skills = Counter(s["name"] for r in resumes for s in r.parsed_data.get("skills", []))
    gaps = Counter(s for m in matches for s in m.result["not_documented_required_skills"])
    return {
        "resumes": len(resumes),
        "applications": len(applications),
        "active_jobs": sum(j.status == "PUBLISHED" for j in jobs),
        "analyses": len(matches),
        "documented_skills": len(skills),
        "ready_resumes": sum(r.status == "COMPLETED" for r in resumes),
        "skills": [{"name": name, "count": count} for name, count in skills.most_common(12)],
        "gaps": [{"name": name, "count": count} for name, count in gaps.most_common(12)],
        "score_distribution": [
            {
                "name": f"{start}–{start + 19 if start < 80 else 100}",
                "count": sum(
                    start <= m.score < start + 20 or (start == 80 and m.score == 100) for m in matches
                ),
            }
            for start in range(0, 100, 20)
        ],
    }
