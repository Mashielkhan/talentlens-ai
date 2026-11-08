import io
import os

import pymupdf
import pytest
from docx import Document
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.session import Base, get_db
from app.main import app
from app.storage.private import storage


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    event.listen(engine, "connect", lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


@pytest.fixture
def client(db, monkeypatch, tmp_path):
    app.dependency_overrides[get_db] = lambda: db
    for module in [
        "app.api.auth",
        "app.api.resumes",
        "app.api.matching",
        "app.api.studio",
        "app.api.account_access",
        "app.api.feedback",
    ]:
        monkeypatch.setattr(module + ".rate_limit", lambda *a, **k: None)
    monkeypatch.setattr(settings(), "storage_path", tmp_path)
    storage.cache_clear()
    with TestClient(app, headers={"Origin": "http://localhost:3000"}) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    storage.cache_clear()


def register(client, email="applicant@example.org", role="APPLICANT"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Synthetic Person",
            "email": email,
            "password": "Correct-Horse-Test-294!",
            "role": role,
            "company": "Synthetic Company" if role == "RECRUITER" else "",
        },
    )
    assert response.status_code == 201, response.text
    client.headers["X-CSRF-Token"] = client.cookies.get("tl_csrf")
    return response.json()


@pytest.fixture
def pdf():
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text(
            (50, 50),
            "Synthetic Person\nsynthetic@example.org\nSkills\nPython, FastAPI, Postgres, Docker\nExperience\nBackend Engineer\nJan 2020 - Jan 2024\nBuilt Python REST APIs using FastAPI and PostgreSQL.\nEducation\nBS Computer Science\nProjects\nBuilt an API with Python.",
        )
        return doc.tobytes()


@pytest.fixture
def docx_bytes():
    doc = Document()
    doc.sections[0].header.paragraphs[0].text = "Synthetic Candidate"
    doc.add_paragraph("Technical Skills")
    table = doc.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "ReactJS and TypeScript"
    table.cell(0, 1).text = "C++ and C#"
    doc.add_paragraph("Education")
    doc.add_paragraph("BS Computer Science, Example University")
    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


@pytest.fixture
def pg_db():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set; PostgreSQL integration not executed")
    engine = create_engine(url)
    with engine.connect() as conn:
        transaction = conn.begin()
        with Session(bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False) as session:
            yield session
        transaction.rollback()
    engine.dispose()
