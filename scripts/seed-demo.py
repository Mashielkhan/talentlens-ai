"""Exercise the real HTTP API. Run only against an isolated DEMO_MODE=true deployment."""

import json
import os
import time
from pathlib import Path

import httpx

BASE = os.getenv("DEMO_API_URL", "http://localhost:8000/api/v1")
ORIGIN = os.getenv("APP_ORIGIN", "http://localhost:3000")
PASSWORD = os.environ.get("DEMO_PASSWORD")
DATA = Path(__file__).resolve().parents[1] / "ml/datasets/generated"


def call(client, method, path, **kwargs):
    client.headers["X-CSRF-Token"] = client.cookies.get("tl_csrf", "")
    response = client.request(method, BASE + path, **kwargs)
    response.raise_for_status()
    return response.json() if response.content else None


def account(client, name, email, role):
    response = client.post(
        BASE + "/auth/register",
        json={
            "full_name": name,
            "email": email,
            "password": PASSWORD,
            "role": role,
            "company": "Synthetic Example Labs",
        },
    )
    if response.status_code == 409:
        call(client, "POST", "/auth/login", json={"email": email, "password": PASSWORD})
    else:
        response.raise_for_status()


def main():
    if not PASSWORD or len(PASSWORD) < 12:
        raise SystemExit(
            "Set DEMO_PASSWORD to a disposable password of at least 12 characters."
        )
    with httpx.Client(headers={"Origin": ORIGIN}, timeout=60) as recruiter:
        if not call(recruiter, "GET", "/health")["demo_mode"]:
            raise SystemExit(
                "Refusing to seed: DEMO_MODE must be true on the isolated target API."
            )
        account(
            recruiter, "Synthetic Recruiter", "recruiter@demo.example.org", "RECRUITER"
        )
        existing = call(recruiter, "GET", "/jobs?mine=true")
        if existing:
            raise SystemExit(
                "Demo jobs already exist. Use an empty isolated demo database for a reproducible seed."
            )
        jobs = [
            call(recruiter, "POST", "/jobs", json=j)
            for j in json.loads((DATA / "jobs.json").read_text())
        ]
        for index, annotation in enumerate(
            json.loads((DATA / "annotations.json").read_text())
        ):
            # Registration throttle is 10/IP/hour: use 5 accounts, 4 documents each.
            with httpx.Client(headers={"Origin": ORIGIN}, timeout=60) as applicant:
                domain = annotation["domain"]
                email = f"applicant{domain + 1}@demo.example.org"
                if annotation["tier"] == 0:
                    account(
                        applicant,
                        f"Synthetic Applicant {domain + 1}",
                        email,
                        "APPLICANT",
                    )
                else:
                    call(
                        applicant,
                        "POST",
                        "/auth/login",
                        json={"email": email, "password": PASSWORD},
                    )
                path = DATA / (annotation["id"] + ".pdf")
                resume = call(
                    applicant,
                    "POST",
                    "/resumes",
                    files={"file": (path.name, path.read_bytes(), "application/pdf")},
                )
                deadline = time.monotonic() + 600
                while time.monotonic() < deadline:
                    state = call(applicant, "GET", "/resumes/" + resume["id"])
                    if state["status"] == "COMPLETED":
                        break
                    if state["status"] == "FAILED":
                        raise RuntimeError(state["error_code"])
                    time.sleep(3)
                else:
                    raise TimeoutError(
                        "Worker did not finish the demo resume within ten minutes"
                    )
                target = jobs[(domain + annotation["tier"]) % len(jobs)]
                call(
                    applicant,
                    "POST",
                    f"/jobs/{target['id']}/applications",
                    json={"resume_id": resume["id"], "consent": True},
                )
                call(
                    applicant,
                    "POST",
                    "/skill-gap/analyze",
                    json={"resume_id": resume["id"], "job_id": jobs[domain]["id"]},
                )
                print(
                    f"Processed synthetic document {index + 1}/20 through the real pipeline"
                )
        for job in jobs:
            call(recruiter, "POST", f"/jobs/{job['id']}/match")
    print(
        "Demo seeded. Sign in as recruiter@demo.example.org or applicant1@demo.example.org using DEMO_PASSWORD. Matching continues in the worker."
    )


if __name__ == "__main__":
    main()
