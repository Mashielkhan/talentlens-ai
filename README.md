# TalentLens AI

**AI-Powered Resume Analyzer & Job Matcher · Mashiel Khan**

**Applicant beta:** CV Studio adds private job-tailored drafts, reviewable wording suggestions, factual approval, and PDF/DOCX CV exports. Account verification/recovery and feedback are implemented with configurable email delivery. See the [beta plan](docs/public-beta-plan.md), [verification record](docs/public-beta-verification.md) and [launch runbook](docs/public-beta-launch.md). Public hosting and email accounts still need to be connected; this repository is not a live public service.

[Public repository](https://github.com/Mashielkhan/talentlens-ai) · [Quality checks](https://github.com/Mashielkhan/talentlens-ai/actions/workflows/ci.yml)

A full-stack portfolio application that turns private PDF/DOCX resumes into editable qualification profiles and compares them with recruiter-confirmed job criteria. Applicants control sharing; recruiters inspect evidence and make their own decisions.

**Status:** implemented application source with automated tests and deployment configuration. See [the implementation record](docs/implementation-status.md) for checks actually executed and remaining work. Do not interpret source coverage as production verification. No hosted demo has been deployed.

**Verification — November 9, 2026:** 53 backend tests (49 unit/API + 3 PostgreSQL integration + 1 real-model test), 6 frontend unit tests and 3 browser scenarios passed locally. The Docker browser checks cover resume processing/corrections, private analysis, consent, recruiter matching, CV editing/approval, PDF/DOCX downloads, failed-save retries, account/password changes, mobile navigation, feedback and deletion. Lint, TypeScript and production builds passed. See the [beta verification record](docs/public-beta-verification.md) for evidence and unverified deployment dependencies. This is a development checkpoint, not a production-readiness or hiring-validity claim.

## What it does

- Applicant and recruiter accounts, Argon2 passwords, HttpOnly server-side sessions, CSRF checks, logout, renewal, password changes and account deletion.
- Private PDF/DOCX uploads with signature/MIME checks, archive expansion limits, text extraction, explicit OCR-required errors, processing states, corrections and reprocessing.
- spaCy general NER, PhraseMatcher skill normalization, section-aware evidence and non-overlapping dated experience.
- Job drafts, publishing, archiving, suggested skills, required/preferred criteria with explicit recruiter review.
- Consent-based applications and withdrawal. Uploading or privately analyzing a resume does **not** make it recruiter-searchable.
- CPU Sentence Transformers, token-aware section chunks, PostgreSQL pgvector storage, exact retrieval over authorized applications, explainable hybrid scoring.
- Deterministic skill gaps and learning suggestions, PDF reports, candidate comparison, and analytics derived from persisted records.
- Private CV Studio drafts from a pasted job description, source-linked editing suggestions, versioned approval and CV PDF/DOCX export. Missing skills are guidance; the app does not invent achievements or silently add qualifications.
- Single-use email verification and password recovery, session revocation after reset, private beta feedback, and a production profile with HTTPS and fail-closed ClamAV scanning.
- Responsive Next.js interface with loading, empty, failure and progress states. No invented candidate rankings or dashboard metrics.

## Architecture

```mermaid
flowchart LR
  Browser[Next.js / React] -->|same-origin API proxy| API[FastAPI]
  API --> DB[(PostgreSQL + pgvector)]
  API --> Storage[Private local or S3 storage]
  API --> Redis[(Redis rate limits)]
  Beat[Celery beat / task outbox] --> DB
  Beat --> Redis
  Redis --> Worker[Celery CPU worker]
  Worker --> Parser[PyMuPDF / python-docx / spaCy]
  Worker --> Models[Sentence Transformers]
  Worker --> DB
  Worker --> Storage
```

The API persists work in a transactional outbox. Celery beat dispatches it, and a worker takes a PostgreSQL advisory lock before processing. Results carry document/job versions, a pinned model revision and a scoring configuration fingerprint. Corrections invalidate previous analyses.

## Stack

Next.js App Router, React, strict TypeScript, Tailwind, shadcn-compatible components, Radix, Lucide, TanStack Query, React Hook Form, Zod, Recharts and Motion. Python 3.12, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 17/pgvector, Redis, Celery, spaCy, Sentence Transformers, PyMuPDF, python-docx and ReportLab. pytest, Ruff, Vitest, Playwright and GitHub Actions.

## Local setup: Docker Desktop

Install Docker Desktop with Linux containers/WSL2 enabled. Keep model downloads on a persistent volume. Allocate resources appropriate to your laptop; 6 GB available RAM is a starting planning estimate, not a measured minimum. Worker concurrency defaults to one and CPU inference uses no GPU.

From this repository directory, in PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose exec worker python -m scripts.warm_models
docker compose logs -f worker
```

Linux/macOS:

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec worker python -m scripts.warm_models
docker compose logs -f worker
```

Open [the application](http://localhost:3000), [interactive API documentation](http://localhost:8000/docs), or [readiness](http://localhost:8000/api/v1/ready). The migration service runs before API/worker startup. First model downloads require internet access and can take several minutes. Do not expose development credentials or local ports publicly.

If port 3000 is already occupied, set both `FRONTEND_PORT=3001` and `APP_ORIGIN=http://localhost:3001` in `.env`, then run `docker compose up -d` and open `http://localhost:3001`. Keep the origin and browser port aligned for CSRF validation.

The default `.env.example` uses explicit **development-only** values. `APP_ORIGIN` must exactly match the browser origin. Production requires HTTPS, `COOKIE_SECURE=true`, private storage and fresh database credentials. Configure S3 using standard AWS credentials outside source control. See [environment and deployment guidance](docs/deployment.md).

### Native development with containerized dependencies

Use Python 3.11/3.12 and Node 22+. Start `docker compose up -d db redis`, then use a virtual environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e './backend[dev]'
python -m spacy download en_core_web_sm
$env:DATABASE_URL='postgresql+psycopg://talentlens:talentlens-local-only@localhost:5432/talentlens'
$env:REDIS_URL='redis://localhost:6379/0'
Set-Location backend
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

On Linux/macOS replace activation with `source .venv/bin/activate` and PowerShell environment assignments with `export NAME=value`. In a second terminal with the same environment, run `celery -A app.workers.tasks:celery worker --concurrency=1` from `backend`; in a third run `celery -A app.workers.tasks:celery beat --schedule=/tmp/talentlens-beat`. Celery's Linux container is the supported worker environment; Windows native workers are not a production target.

Frontend, separate terminal:

```bash
cd frontend
corepack enable
pnpm install --frozen-lockfile
pnpm dev
```

Native API defaults to localhost database/Redis and `backend/data/resumes`. The repository root `.env` is consumed by Compose; native configuration is passed through environment variables to avoid Docker hostnames.

## Demonstrate the real workflow

1. Register a recruiter account. Create a job, classify skills as required/preferred, confirm requirements, and publish.
2. In another browser profile, register an applicant. Upload a PDF/DOCX; wait for completion. Inspect and correct extracted fields.
3. Open the job and choose the processed resume. **Analyze privately** creates an applicant-only report without recruiter access.
4. Inspect score components, effective weights, skill evidence, uncertainties and learning steps. Download the PDF.
5. Check the consent box and submit the application. The recruiter can now inspect this shared resume and run candidate matching.
6. Compare two to four analyses for the same job. Withdraw the application to revoke this job's access. Delete the resume to remove its applications/results and queue physical file deletion.

### Isolated synthetic demo

Generate 20 fictional PDF/DOCX pairs and five jobs with `python scripts/generate-demo.py`. This is **synthetic evaluation/demo data**, not real applicants. The labels are authored for a sanity check; they are not an independently annotated benchmark.

Use a separate Compose project/database for demonstration. Set `DEMO_MODE=true` there, set a disposable password, and seed through the real API:

```powershell
$env:DEMO_PASSWORD='choose-a-disposable-demo-password'
python scripts/seed-demo.py
```

Linux/macOS: `DEMO_PASSWORD='choose-a-disposable-demo-password' python scripts/seed-demo.py`.

Demo account names are printed by the seed script; use the password you supplied. The UI displays a synthetic-demo banner. This local demo is writable and must not be offered as a shared anonymous public sandbox. No production database seeding or paid service provisioning is automatic.

## Matching methodology

The default model is `sentence-transformers/all-MiniLM-L6-v2` pinned to the revision in `.env.example`, producing 384-dimensional vectors. Qualified sections are tokenized and split into overlapping chunks within the model's context limit. Contact details and recognizable demographic lines are excluded; unstructured text can still contain proxies.

The starting heuristic is `0.45 semantic + 0.30 required skills + 0.15 experience + 0.10 education`. Required skill coverage uses recruiter weights. Relevant experience is a union of dated intervals containing required-skill evidence. Education uses conservative documented phrase evidence, not credential equivalence inference. Unknown/not-applicable components are omitted and the remaining weights normalized; all effective weights are exposed. Preferred skills inform explanations and semantic text without being silently made mandatory.

See [the scoring specification](docs/matching-algorithm.md), [NLP pipeline](docs/resume-parsing.md), [taxonomy](docs/skill-normalization.md), [database ER diagram](docs/database.md), and [API contract](docs/api.md).

## Tests and evaluation

```bash
python -m pytest backend/tests -m 'not models'
ruff check backend scripts ml
cd frontend
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm exec playwright install chromium
pnpm test:e2e tests/e2e/public.spec.ts
```

For PostgreSQL integration, point `TEST_DATABASE_URL` at a migrated isolated test database. For real-model tests set `RUN_MODEL_TESTS=1` and run `pytest backend/tests -m models`. For the full browser journey start all services, generate fixtures and set `RUN_FULL_E2E=1 E2E_EXTERNAL=1` before `pnpm test:e2e` (PowerShell uses separate `$env:` assignments).

Measure parsing, skill extraction, ranking baselines and ablations:

```bash
python scripts/generate-demo.py
python ml/evaluation/evaluate.py
```

An optional experimental cross-encoder comparison accepts `--cross-encoder cross-encoder/ms-marco-MiniLM-L-6-v2 --cross-revision <immutable-commit>`. It reports measured latency and ranking changes; it is not enabled in the live product without evaluation. Results are written to `ml/results/` only by executed evaluation. See [evaluation scope and limitations](docs/model-evaluation.md).

## Deployment and limitations

Compose, Dockerfiles, health checks, CI, and an on-demand full validation workflow are included. **No cloud deployment has been performed.** No paid hosting is selected or purchased. [Deployment instructions](docs/deployment.md) cover secrets, storage, reverse proxies and rollback. [Security](docs/security.md), [privacy](docs/privacy.md), [limitations](docs/limitations.md), and [troubleshooting](docs/troubleshooting.md) distinguish safeguards from unverified production requirements.

OCR, verified email recovery, custom resume-domain NER, multilingual support, production malware scanning, a read-only public demo, and independently validated fairness/ranking quality remain future work. Structured education/employment extraction is conservative and needs human review. The initial schema consolidates some profile fields into JSONB rather than creating empty relational tables.

## Portfolio

See [portfolio presentation](docs/portfolio-presentation.md) for a walkthrough, truthful CV wording, and suggested screenshots. Screenshots, when captured, are stored in `docs/screenshots/`; no fabricated product results are presented as evidence.

Author: **Mashiel Khan**. Source licensing and third-party notices are described in [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
