import io
import socket
import socketserver
import threading
import uuid
from datetime import UTC, datetime, timedelta
from email import message_from_string, policy
from queue import Queue

import pymupdf
import pytest
from conftest import register
from docx import Document
from sqlalchemy import select

from app.core.config import Settings, settings
from app.core.security import digest
from app.models.entities import AccountToken, CvDraft, Resume
from app.services.cv_studio import prepare_draft, render_cv
from app.services.upload_scan import scan_upload


def ready_resume(client, db, pdf):
    register(client)
    result = client.post("/api/v1/resumes", files={"file": ("test.pdf", pdf, "application/pdf")})
    resume = db.get(Resume, uuid.UUID(result.json()["id"]))
    resume.status = "COMPLETED"
    resume.parsed_data = {
        "contact": {"name": "Synthetic Person", "email": "synthetic@example.org"},
        "sections": {
            "experience": "I developed Python APIs in order to process 20 requests.",
            "education": "BS Computer Science",
        },
        "skills": [{"name": "Python"}],
    }
    db.commit()
    return resume


def make_draft(client, resume):
    response = client.post(
        "/api/v1/studio",
        json={
            "resume_id": str(resume.id),
            "title": "Backend role",
            "target_description": "Develop Python and FastAPI services with Docker containers.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_draft_approval_revision_conflicts_and_export(client, db, pdf):
    resume = ready_resume(client, db, pdf)
    draft = make_draft(client, resume)
    url = f"/api/v1/studio/{draft['id']}"
    assert draft["content"] == draft["original"]
    assert "FastAPI" in draft["guidance"]["not_documented_target_skills"]
    assert "FastAPI" not in draft["content"]["skills"]
    assert client.get(url + "/export/pdf").status_code == 409
    replacement = draft["guidance"]["suggestions"][0]["replacement"]
    assert "20 requests" in replacement and replacement.startswith("Developed Python")
    edited = {**draft["content"], "experience": replacement}
    assert client.patch(url, json={"revision": 1, "content": edited}).status_code == 200
    assert client.patch(url, json={"revision": 1, "content": edited}).status_code == 409
    assert client.post(url + "/approve", json={"revision": 1, "facts_confirmed": True}).status_code == 409
    assert client.post(url + "/approve", json={"revision": 2, "facts_confirmed": False}).status_code == 422
    assert client.post(url + "/approve", json={"revision": 2, "facts_confirmed": True}).status_code == 200
    pdf_result = client.get(url + "/export/pdf")
    assert pdf_result.status_code == 200
    with pymupdf.open(stream=pdf_result.content, filetype="pdf") as document:
        text = "".join(p.get_text() for p in document)
        assert "20 requests" in text and "Compatibility Index" not in text
    docx_result = client.get(url + "/export/docx")
    document = Document(io.BytesIO(docx_result.content))
    assert replacement in "\n".join(p.text for p in document.paragraphs)
    assert client.patch(url, json={"revision": 2, "content": edited}).status_code == 200
    assert client.get(url + "/export/docx").status_code == 409


def test_draft_isolation_source_change_and_cascade(client, db, pdf):
    resume = ready_resume(client, db, pdf)
    draft = make_draft(client, resume)
    url = f"/api/v1/studio/{draft['id']}"
    owner_cookies = dict(client.cookies)
    register(client, "other-beta@example.org")
    assert client.get(url).status_code == 404
    assert client.get(url + "/export/pdf").status_code == 404
    assert client.delete(url).status_code == 404
    register(client, "recruiter-beta@example.org", "RECRUITER")
    assert client.get(url).status_code == 403
    client.cookies.clear()
    client.cookies.update(owner_cookies)
    client.headers["X-CSRF-Token"] = owner_cookies["tl_csrf"]
    resume.version += 1
    db.commit()
    assert client.get(url).json()["source_outdated"] is True
    assert client.post(url + "/approve", json={"revision": 1, "facts_confirmed": True}).status_code == 409
    assert client.patch(url, json={"revision": 1, "content": draft["content"]}).status_code == 409
    assert client.delete(f"/api/v1/resumes/{resume.id}").status_code == 204
    assert db.scalar(select(CvDraft.id)) is None


def test_cv_exports_escape_markup_and_paginate():
    content = {
        "name": "Zoë Example",
        "experience": "\n".join(f"Built <safe> & documented service {i}." for i in range(150)),
    }
    data = render_cv(content, "pdf")
    with pymupdf.open(stream=data, filetype="pdf") as document:
        text = "".join(p.get_text() for p in document)
        assert len(document) > 1 and "service 149" in text and "<safe>" in text and "Zoë" in text
    doc = Document(io.BytesIO(render_cv(content, "docx")))
    assert "service 149" in doc.paragraphs[-1].text


def test_editing_rules_do_not_invent_metrics_or_missing_skills():
    content, guidance = prepare_draft(
        {"sections": {"projects": "I built a tool. I did not use Docker."}, "skills": []},
        "Develop Kubernetes and Docker services for a Python application.",
    )
    assert content["projects"] == "I built a tool. I did not use Docker."
    assert guidance["suggestions"][0]["replacement"] == "Built a tool. I did not use Docker."
    assert content["skills"] == ""


def test_unsupported_pdf_glyphs_offer_docx_instead_of_broken_text():
    with pytest.raises(ValueError, match="DOCX"):
        render_cv({"name": "Synthetic Applicant", "summary": "Testing 🧪"}, "pdf")
    doc = Document(io.BytesIO(render_cv({"name": "Synthetic Applicant", "summary": "Testing 🧪"}, "docx")))
    assert doc.paragraphs[-1].text == "Testing 🧪"


@pytest.fixture
def delivered(monkeypatch):
    messages = []
    monkeypatch.setattr(settings(), "smtp_host", "test-mail")
    monkeypatch.setattr(settings(), "smtp_from", "beta@example.org")
    monkeypatch.setattr(
        "app.services.account_mail.send_account_mail",
        lambda address, purpose, token: messages.append((address, purpose, token)),
    )
    return messages


def test_recovery_is_generic_single_use_and_revokes_sessions(client, db, delivered):
    register(client)
    cookies = dict(client.cookies)
    known = client.post("/api/v1/auth/request-password-reset", json={"email": "applicant@example.org"})
    unknown = client.post("/api/v1/auth/request-password-reset", json={"email": "absent@example.org"})
    assert known.status_code == unknown.status_code == 202 and known.json() == unknown.json()
    raw = delivered[0][2]
    token = db.scalar(select(AccountToken))
    assert token.token_hash == digest(raw) and raw not in known.text
    assert client.post("/api/v1/auth/verify-email", json={"token": raw}).status_code == 400
    reset = {"token": raw, "new_password": "New-correct-horse-2048!"}
    assert client.post("/api/v1/auth/reset-password", json=reset).status_code == 204
    assert client.post("/api/v1/auth/reset-password", json=reset).status_code == 400
    client.cookies.update(cookies)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "applicant@example.org", "password": reset["new_password"]}
        ).status_code
        == 200
    )


def test_verification_gate_expiry_and_resend(client, db, delivered, monkeypatch, pdf):
    register(client)
    monkeypatch.setattr(settings(), "require_email_verification", True)
    assert (
        client.post("/api/v1/resumes", files={"file": ("r.pdf", pdf, "application/pdf")}).status_code == 403
    )
    assert client.post("/api/v1/auth/request-verification").status_code == 202
    old = delivered[-1][2]
    token = db.scalar(select(AccountToken))
    token.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db.commit()
    assert client.post("/api/v1/auth/verify-email", json={"token": old}).status_code == 400
    assert client.post("/api/v1/auth/request-verification").status_code == 202
    new = delivered[-1][2]
    assert old != new
    assert client.post("/api/v1/auth/verify-email", json={"token": old}).status_code == 400
    assert client.post("/api/v1/auth/verify-email", json={"token": new}).status_code == 204
    assert client.post("/api/v1/auth/verify-email", json={"token": new}).status_code == 400
    assert client.get("/api/v1/auth/me").json()["email_verified"] is True
    assert (
        client.post("/api/v1/resumes", files={"file": ("r.pdf", pdf, "application/pdf")}).status_code == 202
    )


def test_password_change_invalidates_recovery_links(client, db, delivered):
    register(client)
    client.post("/api/v1/auth/request-password-reset", json={"email": "applicant@example.org"})
    raw = delivered[-1][2]
    assert (
        client.post(
            "/api/v1/auth/password",
            json={"current_password": "Correct-Horse-Test-294!", "new_password": "Changed-password-2048!"},
        ).status_code
        == 204
    )
    assert (
        client.post(
            "/api/v1/auth/reset-password", json={"token": raw, "new_password": "Attacker-password-2048!"}
        ).status_code
        == 400
    )


def test_email_unconfigured_and_feedback(client, monkeypatch):
    monkeypatch.setattr(settings(), "smtp_host", "")
    assert client.get("/api/v1/auth/config").json()["email_available"] is False
    assert (
        client.post("/api/v1/auth/request-password-reset", json={"email": "absent@example.org"}).status_code
        == 503
    )
    assert (
        client.post("/api/v1/feedback", json={"category": "bug", "message": "A synthetic issue"}).status_code
        == 401
    )
    register(client)
    assert (
        client.post("/api/v1/feedback", json={"category": "bug", "message": "A synthetic issue"}).status_code
        == 201
    )


def test_account_mail_over_local_smtp_socket(monkeypatch):
    from app.services.account_mail import send_account_mail

    messages = Queue()

    class Mailbox(socketserver.StreamRequestHandler):
        def handle(self):
            self.wfile.write(b"220 synthetic-mail ESMTP\r\n")
            while line := self.rfile.readline():
                command = line.split(b" ", 1)[0].strip().upper()
                if command == b"DATA":
                    self.wfile.write(b"354 End with dot\r\n")
                    content = []
                    while (part := self.rfile.readline()) not in (b".\r\n", b""):
                        content.append(part)
                    messages.put(b"".join(content).decode())
                    self.wfile.write(b"250 Accepted\r\n")
                elif command == b"QUIT":
                    self.wfile.write(b"221 Bye\r\n")
                    return
                else:
                    self.wfile.write(b"250 OK\r\n")

    with socketserver.TCPServer(("127.0.0.1", 0), Mailbox) as mailbox:
        thread = threading.Thread(target=mailbox.serve_forever, daemon=True)
        thread.start()
        monkeypatch.setattr(settings(), "smtp_host", "127.0.0.1")
        monkeypatch.setattr(settings(), "smtp_port", mailbox.server_address[1])
        monkeypatch.setattr(settings(), "smtp_from", "beta@example.org")
        monkeypatch.setattr(settings(), "smtp_security", "none")
        monkeypatch.setattr(settings(), "smtp_username", "")
        try:
            send_account_mail("synthetic@example.org", "reset", "synthetic-token-only")
            message = messages.get(timeout=2)
            decoded = message_from_string(message, policy=policy.default)
            assert "reset-password#token=synthetic-token-only" in decoded.get_content()
            assert "Subject: Reset your TalentLens password" in message
            assert "To: synthetic@example.org" in message
        finally:
            mailbox.shutdown()
            thread.join(timeout=2)


@pytest.mark.parametrize(
    "answer,code",
    [(b"stream: OK\0", None), (b"stream: Eicar FOUND\0", 422), (b"stream: scan ERROR\0", 503), (b"", 503)],
)
def test_scan_fails_closed(monkeypatch, answer, code):
    from fastapi import HTTPException

    class Scanner:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def settimeout(self, timeout):
            pass

        def sendall(self, data):
            pass

        def recv(self, size):
            return answer

    monkeypatch.setattr(settings(), "upload_scanning", "clamav")
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: Scanner())
    if code:
        with pytest.raises(HTTPException) as error:
            scan_upload(b"synthetic")
        assert error.value.status_code == code
    else:
        scan_upload(b"synthetic")


def test_production_requires_email_and_scanning():
    with pytest.raises(ValueError, match="verification"):
        Settings(
            _env_file=None,
            environment="production",
            cookie_secure=True,
            app_origin="https://beta.example.org",
            database_url="postgresql+psycopg://beta:test-only@db/beta",
        )
