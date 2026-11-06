import uuid

from sqlalchemy import delete, func, select

from app.ml.embeddings import embed_sections, model_version, semantic_score
from app.ml.scoring import score_match
from app.models.entities import Application, Job, JobSection, MatchResult, Resume, ResumeSection
from app.nlp.documents import extract_text
from app.nlp.parser import parse_resume, qualification_texts
from app.storage.private import storage


def process_resume(db, task):
    resume = db.get(Resume, task.resume_id)
    if not resume or resume.version != task.payload["version"]:
        return {"superseded": True}
    version = resume.version
    text = extract_text(storage().read(resume.storage_key), "." + resume.storage_key.rsplit(".", 1)[1])
    parsed = parse_resume(text, resume.corrections)
    vectors = embed_sections(qualification_texts(parsed))
    # Lock after expensive work and recheck the version; corrections/deletions win.
    db.expire_all()
    resume = db.scalar(select(Resume).where(Resume.id == task.resume_id).with_for_update())
    if not resume or resume.version != version:
        return {"superseded": True}
    db.execute(delete(ResumeSection).where(ResumeSection.resume_id == resume.id))
    for section, chunk, vector in vectors:
        db.add(
            ResumeSection(
                resume_id=resume.id,
                section_type=section,
                text=chunk,
                embedding=vector,
                model_version=model_version(),
            )
        )
    resume.raw_text, resume.parsed_data = text, parsed
    resume.status, resume.stage, resume.error_code = "COMPLETED", "Ready for review", None
    resume.model_version = model_version()
    return {"resume_id": str(resume.id)}


def job_vectors(db, job):
    rows = db.scalars(
        select(JobSection).where(
            JobSection.job_id == job.id,
            JobSection.version == job.version,
            JobSection.model_version == model_version(),
        )
    ).all()
    if rows:
        return [row.embedding for row in rows]
    # Company/title/location are deliberately excluded from semantic input.
    sections = {
        "description": job.description,
        "required": ", ".join(s["name"] for s in job.required_skills),
        "preferred": ", ".join(s["name"] for s in job.preferred_skills),
    }
    chunks = embed_sections(sections)
    db.execute(delete(JobSection).where(JobSection.job_id == job.id))
    for _, chunk, vector in chunks:
        db.add(
            JobSection(
                job_id=job.id,
                text=chunk,
                embedding=vector,
                version=job.version,
                model_version=model_version(),
            )
        )
    return [vector for _, _, vector in chunks]


def authorized_retrieval(db, job, vectors, limit=100):
    """Exact pgvector retrieval scoped by consent before any ranking/limit."""
    distance = func.min(ResumeSection.embedding.cosine_distance(vectors[0]))
    query = (
        select(Application, distance.label("distance"))
        .join(Resume, Resume.id == Application.resume_id)
        .join(ResumeSection, ResumeSection.resume_id == Resume.id)
        .where(
            Application.job_id == job.id,
            Resume.status == "COMPLETED",
            ResumeSection.model_version == model_version(),
        )
        .group_by(Application.id)
        .order_by(distance, Application.id)
        .limit(limit)
    )
    return [row[0] for row in db.execute(query).all()]


def run_matching(db, task):
    job = db.scalar(select(Job).where(Job.id == task.job_id).with_for_update())
    if not job or not job.requirements_confirmed or job.version != task.payload["job_version"]:
        raise ValueError("JOB_CHANGED_RETRY_MATCHING")
    if task.kind == "MATCH_JOB" and job.recruiter_id != task.owner_id:
        raise ValueError("ACCESS_REVOKED")
    jvectors = job_vectors(db, job)
    candidates = []
    if task.kind == "ANALYZE":
        if job.status != "PUBLISHED":
            raise ValueError("JOB_NOT_PUBLISHED")
        resume = db.scalar(
            select(Resume)
            .where(Resume.id == task.resume_id, Resume.owner_id == task.owner_id)
            .with_for_update()
        )
        if not resume or resume.status != "COMPLETED":
            raise ValueError("RESUME_NOT_READY")
        candidates = [(resume, None)]
    else:
        for application in authorized_retrieval(db, job, jvectors):
            # Serialize with resume corrections and application withdrawal.
            application = db.scalar(
                select(Application).where(Application.id == application.id).with_for_update()
            )
            if application:
                resume = db.scalar(select(Resume).where(Resume.id == application.resume_id).with_for_update())
                if resume and resume.status == "COMPLETED":
                    candidates.append((resume, application))
    results = []
    for resume, application in candidates:
        rvectors = db.scalars(
            select(ResumeSection).where(
                ResumeSection.resume_id == resume.id, ResumeSection.model_version == model_version()
            )
        ).all()
        result = score_match(
            resume.parsed_data, job, semantic_score([r.embedding for r in rvectors], jvectors)
        )
        result.update(
            {
                "job_title": job.title,
                "company": job.company,
                "resume_filename": resume.original_filename,
                "model_version": model_version(),
                "as_of_date": resume.parsed_data["as_of_date"],
            }
        )
        # Replace only this audience's result, preserving applicant-only analyses.
        query = delete(MatchResult).where(
            MatchResult.job_id == job.id,
            MatchResult.resume_id == resume.id,
            MatchResult.requester_id == task.owner_id,
        )
        db.execute(query)
        match = MatchResult(
            id=uuid.uuid4(),
            job_id=job.id,
            resume_id=resume.id,
            requester_id=task.owner_id,
            application_id=application.id if application else None,
            job_version=job.version,
            resume_version=resume.version,
            score=result["compatibility_index"],
            result=result,
            model_version=model_version(),
            scoring_version=result["scoring_version"],
        )
        db.add(match)
        results.append(str(match.id))
    return {"match_ids": results, "candidate_count": len(results), "retrieval_limit": 100}
