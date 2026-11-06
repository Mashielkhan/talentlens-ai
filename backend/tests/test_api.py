import uuid

from conftest import register
from sqlalchemy import select

from app.core.security import hasher, verify_password
from app.models.entities import Deletion, MatchResult, Resume, User


def job_payload(**overrides):
    return {
        "title": "Python Engineer",
        "company": "Synthetic Company",
        "description": "Build maintainable Python APIs with FastAPI and PostgreSQL for a synthetic test.",
        "required_skills": [{"name": "Python", "weight": 5}],
        "status": "PUBLISHED",
        "requirements_confirmed": True,
        **overrides,
    }


def test_auth_csrf_and_logout(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    register(client)
    assert client.get("/api/v1/auth/me").status_code == 200
    assert "HttpOnly" in client.cookies.jar._cookies["testserver.local"]["/"]["tl_session"]._rest
    client.headers.pop("X-CSRF-Token")
    assert client.post("/api/v1/auth/logout").status_code == 403
    client.headers["X-CSRF-Token"] = client.cookies.get("tl_csrf")
    assert client.post("/api/v1/auth/logout").status_code == 204
    assert client.get("/api/v1/auth/me").status_code == 401


def test_origin_and_role_boundaries(client):
    assert (
        client.post("/api/v1/auth/login", json={}, headers={"Origin": "https://evil.invalid"}).status_code
        == 403
    )
    register(client)
    assert client.post("/api/v1/jobs", json=job_payload()).status_code == 403
    assert (
        client.post(
            "/api/v1/auth/register",
            json={
                "full_name": "Attack",
                "email": "admin@example.org",
                "password": "long-password-123",
                "role": "ADMIN",
            },
        ).status_code
        == 422
    )


def test_registration_password_and_login(client):
    register(client)
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "applicant@example.org", "password": "wrong"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login",
            json={"email": "applicant@example.org", "password": "Correct-Horse-Test-294!"},
        ).status_code
        == 200
    )
    assert verify_password(hasher.hash("a password"), "a password")


def test_private_upload_cross_user_and_delete(client, db, pdf):
    register(client)
    response = client.post("/api/v1/resumes", files={"file": ("../../resume.pdf", pdf, "application/pdf")})
    assert response.status_code == 202, response.text
    resume_id = response.json()["id"]
    assert response.json()["original_filename"] == "resume.pdf"
    assert "storage_key" not in response.json()
    assert client.get(f"/api/v1/resumes/{resume_id}/download").content == pdf
    first_cookies = dict(client.cookies)
    register(client, "another@example.org")
    assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 404
    assert client.get(f"/api/v1/resumes/{resume_id}/download").status_code == 404
    assert client.delete(f"/api/v1/resumes/{resume_id}").status_code == 404
    client.cookies.clear()
    client.cookies.update(first_cookies)
    client.headers["X-CSRF-Token"] = first_cookies["tl_csrf"]
    assert client.delete(f"/api/v1/resumes/{resume_id}").status_code == 204
    assert client.get(f"/api/v1/resumes/{resume_id}/download").status_code == 404
    assert db.scalar(select(Deletion)) is not None


def test_recruiter_only_sees_consented_resumes(client, db, pdf):
    register(client, "recruiter@example.org", "RECRUITER")
    job = client.post("/api/v1/jobs", json=job_payload()).json()
    recruiter_cookies = dict(client.cookies)
    register(client, "owner@example.org")
    resume_id = client.post("/api/v1/resumes", files={"file": ("r.pdf", pdf, "application/pdf")}).json()["id"]
    resume = db.get(Resume, uuid.UUID(resume_id))
    resume.status = "COMPLETED"  # Authorization test only, no inference claimed.
    db.commit()
    applicant_cookies = dict(client.cookies)
    client.cookies.clear()
    client.cookies.update(recruiter_cookies)
    client.headers["X-CSRF-Token"] = recruiter_cookies["tl_csrf"]
    assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 404
    client.cookies.clear()
    client.cookies.update(applicant_cookies)
    client.headers["X-CSRF-Token"] = applicant_cookies["tl_csrf"]
    assert (
        client.post(
            f"/api/v1/jobs/{job['id']}/applications", json={"resume_id": resume_id, "consent": False}
        ).status_code
        == 422
    )
    response = client.post(
        f"/api/v1/jobs/{job['id']}/applications", json={"resume_id": resume_id, "consent": True}
    )
    assert response.status_code == 201, response.text
    app_id = response.json()["id"]
    client.cookies.clear()
    client.cookies.update(recruiter_cookies)
    client.headers["X-CSRF-Token"] = recruiter_cookies["tl_csrf"]
    assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 200
    assert len(client.get(f"/api/v1/jobs/{job['id']}/applications").json()) == 1
    client.cookies.clear()
    client.cookies.update(applicant_cookies)
    client.headers["X-CSRF-Token"] = applicant_cookies["tl_csrf"]
    assert client.delete(f"/api/v1/applications/{app_id}").status_code == 204
    client.cookies.clear()
    client.cookies.update(recruiter_cookies)
    client.headers["X-CSRF-Token"] = recruiter_cookies["tl_csrf"]
    assert client.get(f"/api/v1/resumes/{resume_id}").status_code == 404


def test_draft_cross_recruiter_and_confirmation(client):
    register(client, "rec1@example.org", "RECRUITER")
    assert client.post("/api/v1/jobs", json=job_payload(requirements_confirmed=False)).status_code == 422
    draft = client.post("/api/v1/jobs", json=job_payload(status="DRAFT")).json()
    register(client, "rec2@example.org", "RECRUITER")
    assert client.get(f"/api/v1/jobs/{draft['id']}").status_code == 404
    assert client.patch(f"/api/v1/jobs/{draft['id']}", json=job_payload()).status_code == 404
    assert client.post(f"/api/v1/jobs/{draft['id']}/match").status_code == 404


def test_mime_upload_errors(client, pdf):
    register(client)
    assert client.post("/api/v1/resumes", files={"file": ("r.pdf", pdf, "image/png")}).status_code == 422


def test_account_delete_revokes_data(client, db, pdf):
    register(client)
    resume = client.post("/api/v1/resumes", files={"file": ("r.pdf", pdf, "application/pdf")}).json()
    response = client.request(
        "DELETE",
        "/api/v1/auth/account",
        json={"email": "applicant@example.org", "password": "Correct-Horse-Test-294!"},
    )
    assert response.status_code == 204, response.text
    assert db.get(Resume, uuid.UUID(resume["id"])) is None
    assert db.scalar(select(User)) is None
    assert client.get("/api/v1/auth/me").status_code == 401


def test_matching_invalidated_by_job_edit(client, db, pdf):
    applicant = register(client)
    resume_id = client.post("/api/v1/resumes", files={"file": ("r.pdf", pdf, "application/pdf")}).json()["id"]
    recruiter = register(client, "rec@example.org", "RECRUITER")
    job = client.post("/api/v1/jobs", json=job_payload()).json()
    db.add(
        MatchResult(
            job_id=uuid.UUID(job["id"]),
            resume_id=uuid.UUID(resume_id),
            requester_id=uuid.UUID(applicant["id"]),
            job_version=1,
            resume_version=1,
            score=70,
            result={},
            model_version="unit-test",
            scoring_version="unit-test",
        )
    )
    db.commit()
    assert (
        client.patch(
            f"/api/v1/jobs/{job['id']}", json=job_payload(title="Revised Backend Engineer")
        ).status_code
        == 200
    )
    assert db.scalar(select(MatchResult)) is None
    assert recruiter["role"] == "RECRUITER"
