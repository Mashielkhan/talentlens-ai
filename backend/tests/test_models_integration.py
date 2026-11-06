import os
from datetime import date

import pytest
from sqlalchemy import delete, select, text

from app.ml.embeddings import embed_sections, model_version, semantic_score
from app.models.entities import Application, Job, MatchResult, Resume, ResumeSection, User
from app.nlp.parser import parse_resume, qualification_texts
from app.services.processing import authorized_retrieval


@pytest.mark.integration
def test_postgres_migration_vector_and_fts(pg_db):
    assert pg_db.scalar(text("SELECT version_num FROM alembic_version")) == "0001"
    assert pg_db.scalar(text("SELECT '[1,0,0]'::vector <=> '[1,0,0]'::vector")) == 0
    assert pg_db.scalar(
        text(
            "SELECT to_tsvector('english', 'Python backend engineer') @@ websearch_to_tsquery('english', 'backend')"
        )
    )


@pytest.mark.integration
def test_vector_retrieval_filters_consent_and_model_before_limit(pg_db):
    """Controlled vector fixtures test SQL isolation, not model prediction quality."""
    recruiter = User(
        email="pg-rec@example.org",
        full_name="Synthetic Recruiter",
        password_hash="test-only",
        role="RECRUITER",
    )
    applicant = User(
        email="pg-app@example.org",
        full_name="Synthetic Applicant",
        password_hash="test-only",
        role="APPLICANT",
    )
    stale_applicant = User(
        email="pg-stale@example.org",
        full_name="Synthetic Stale Applicant",
        password_hash="test-only",
        role="APPLICANT",
    )
    pg_db.add_all([recruiter, applicant, stale_applicant])
    pg_db.flush()
    job = Job(
        recruiter_id=recruiter.id,
        title="Synthetic backend role",
        company="Test",
        description="Test qualifications",
        status="PUBLISHED",
        requirements_confirmed=True,
    )
    pg_db.add(job)
    pg_db.flush()
    resumes = []
    for i in range(3):
        resume = Resume(
            owner_id=stale_applicant.id if i == 2 else applicant.id,
            original_filename=f"synthetic-{i}.pdf",
            storage_key=f"integration-{i}.pdf",
            mime_type="application/pdf",
            file_size=100,
            file_hash=str(i),
            status="COMPLETED",
        )
        pg_db.add(resume)
        pg_db.flush()
        resumes.append(resume)
        vector = [1.0] + [0.0] * 383 if i != 1 else [0.8, 0.6] + [0.0] * 382
        pg_db.add(
            ResumeSection(
                resume_id=resume.id,
                section_type="skills",
                text="Synthetic vector fixture",
                embedding=vector,
                model_version=model_version() if i != 2 else "obsolete-model",
            )
        )
    # The unshared perfect match and the obsolete model must not crowd out the
    # consented, current-model applicant when retrieval is limited to one.
    application = Application(job_id=job.id, applicant_id=applicant.id, resume_id=resumes[1].id)
    pg_db.add(application)
    pg_db.add(Application(job_id=job.id, applicant_id=stale_applicant.id, resume_id=resumes[2].id))
    pg_db.flush()
    retrieved = authorized_retrieval(pg_db, job, [[1.0] + [0.0] * 383], limit=1)
    assert [item.id for item in retrieved] == [application.id]
    pg_db.delete(application)
    pg_db.flush()
    assert authorized_retrieval(pg_db, job, [[1.0] + [0.0] * 383], limit=1) == []


@pytest.mark.integration
def test_postgres_cascades_shared_results_on_withdrawal(pg_db):
    owner = User(
        email="pg-owner@example.org", full_name="Synthetic Owner", password_hash="test-only", role="APPLICANT"
    )
    recruiter = User(
        email="pg-company@example.org",
        full_name="Synthetic Recruiter",
        password_hash="test-only",
        role="RECRUITER",
    )
    pg_db.add_all([owner, recruiter])
    pg_db.flush()
    resume = Resume(
        owner_id=owner.id,
        original_filename="test.pdf",
        storage_key="cascade-test.pdf",
        mime_type="application/pdf",
        file_size=100,
        file_hash="test",
    )
    job = Job(recruiter_id=recruiter.id, title="Test job", company="Test", description="Test job criteria")
    pg_db.add_all([resume, job])
    pg_db.flush()
    application = Application(job_id=job.id, applicant_id=owner.id, resume_id=resume.id)
    pg_db.add(application)
    pg_db.flush()
    common = dict(
        job_id=job.id,
        resume_id=resume.id,
        job_version=1,
        resume_version=1,
        score=0,
        result={},
        model_version="fixture",
        scoring_version="fixture",
    )
    private_result = MatchResult(requester_id=owner.id, **common)
    shared_result = MatchResult(requester_id=recruiter.id, application_id=application.id, **common)
    pg_db.add_all([private_result, shared_result])
    pg_db.flush()
    pg_db.execute(delete(Application).where(Application.id == application.id))
    remaining = pg_db.scalars(select(MatchResult.id).where(MatchResult.resume_id == resume.id)).all()
    assert remaining == [private_result.id]


@pytest.mark.models
def test_real_model_prefers_backend_and_is_stable():
    if os.environ.get("RUN_MODEL_TESTS") != "1":
        pytest.skip("Set RUN_MODEL_TESTS=1 to execute downloaded models")
    backend = "Synthetic Person\nSkills\nPython FastAPI PostgreSQL Docker\nExperience\nJan 2020 - Jan 2024\nBuilt Python backend REST APIs with FastAPI and PostgreSQL."
    frontend = "Other Person\nSkills\nReact CSS TypeScript\nExperience\nJan 2020 - Jan 2024\nDesigned responsive React components and CSS layouts."
    vectors = []
    for document in [backend, frontend]:
        parsed = parse_resume(document, today=date(2026, 1, 1))
        vectors.append([v for _, _, v in embed_sections(qualification_texts(parsed))])
    job = [
        v
        for _, _, v in embed_sections(
            {"description": "Build Python backend REST APIs using FastAPI and PostgreSQL."}
        )
    ]
    a, b = [semantic_score(v, job) for v in vectors]
    assert a > b
    repeated = [
        v
        for _, _, v in embed_sections(
            {"description": "Build Python backend REST APIs using FastAPI and PostgreSQL."}
        )
    ]
    assert semantic_score(vectors[0], repeated) == pytest.approx(a, abs=1e-4)
