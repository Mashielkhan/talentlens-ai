# Implementation status

This file distinguishes implemented source from executed verification. Checkpoint recorded on November 6, 2026. The owner authorized continued Docker integration validation and public GitHub publication after the unit-test checkpoint.

## Review checkpoint

| Executed check | Result |
|---|---|
| Backend unit/API-isolation tests | **34 passed**, 2 integration/model tests deliberately deselected; 5.37 seconds for the final test run |
| Frontend Vitest tests | **4 passed** in 2 test files |
| Ruff (`backend scripts ml`) | Passed |
| ESLint | Passed with no remaining warnings/errors |
| TypeScript `tsc --noEmit` | Passed |
| Next.js production build (`next build --webpack`) | Passed; 12 static pages generated and dynamic detail routes compiled |
| Python source compilation | Passed |

The API-isolation tests use an in-memory SQLite fixture and replace Redis throttling. They exercise real API validation, Argon2/session authentication, CSRF/origin checks, ownership/consent rules, uploads, deletion and invalidation, but do **not** verify PostgreSQL, Redis or Celery integration. Parsing tests execute PyMuPDF, python-docx and spaCy PhraseMatcher; pretrained NER and Sentence Transformer inference have not been executed here.

The test run found and fixed nested skill alias duplication: `React JS` no longer separately asserts JavaScript, and `Postgre SQL` no longer separately asserts SQL. The matcher now selects the longest non-overlapping phrases. Python/frontend formatting and import lint issues were fixed without weakening test assertions.

### Environment issues encountered

- Pytest's default temporary directory was not writable in the sandbox; final verification used a dedicated workspace-local temp directory.
- Windows asyncio's internal loopback socket pair hung in the network sandbox. The final backend suite ran with approved execution outside that sandbox; the diagnostic trace located the hang before API test startup.
- The default Turbopack build failed spawning its CSS subprocess. A sandboxed Webpack build also hit generated-directory permissions. The approved Webpack build outside the sandbox completed successfully.
- Browser smoke tests were attempted but did **not** pass: sandbox network access was denied, and a subsequent external browser could not reach the sandboxed server. Browser/UI verification is still pending, not counted as a passing check.
- Installed backend test subset includes Python 3.12.14, FastAPI 0.162.0, SQLAlchemy 2.0.57, pytest 9.2.0, spaCy 3.8.18, PyMuPDF 1.28.2 and ReportLab 4.5.1. The full Sentence Transformers/S3/evaluation dependency set and pretrained models are not yet installed. A Starlette warning notes future deprecation of its httpx test-client adapter; it did not fail any test.

### Integration validation in progress

Docker Desktop is now installed and the Linux engine is running. Initial service images and application dependencies are downloading. Next: validate PostgreSQL migrations/vector queries, Redis and Celery processing, install/warm real models, run the applicant/recruiter browser journey, and measure synthetic evaluation. Do not treat this unit-test checkpoint as a deployed or fully end-to-end-validated product.

| Phase | Source status | Verification / remaining work |
|---|---|---|
| 1. Setup | Next.js, FastAPI, PostgreSQL/pgvector, Redis/Celery, Compose, health/readiness | Frontend build and backend imports/tests passed. Docker unavailable; live services unverified. |
| 2. Authentication | Argon2, opaque server-side sessions, CSRF, role/object authorization, settings/deletion | API-isolation authorization tests passed. No email recovery provider. |
| 3. Documents | Private local/S3 storage, bounded PDF/DOCX validation, extraction, corrections, reprocessing | Document parsing/safety tests passed. S3 not tested. OCR explicitly unsupported. |
| 4. NLP | spaCy NER, PhraseMatcher taxonomy, sections, contact regex, dated experience with overlap union | Structured employment/education fields remain heuristic; narrative evidence preserved. Model evaluation pending installation. |
| 5. Jobs | Draft/publish/archive, requirements review, weighted skills, application consent and withdrawal | Frontend and backend connected in source; live integration not yet executed. |
| 6. Matching | Pinned MiniLM model, token-aware chunks, vector persistence and authorized exact retrieval, hybrid scoring | Requires actual model downloads and PostgreSQL for live verification. |
| 7. Explainability | Effective weights, evidence, uncertainty, deterministic gaps/resources, private PDF exports | Scoring and PDF content/pagination tests passed. Human visual report review pending. |
| 8. Advanced retrieval | Exact pgvector shortlist of 100; optional offline cross-encoder experiment runner | No real retrieval/reranking benchmark executed. No quality claims. |
| 9. UI | Landing, auth, dashboards, resume/profile editing, jobs, matching, comparison, analytics, settings | Unit tests, lint, TypeScript and Webpack build passed. Browser verification pending. |
| 10. Testing | Unit-test checkpoint reached | 34 backend + 4 frontend tests passed; full service/model/browser tests pending. |
| 11. Deployment | Compose and Dockerfiles | No deployment performed. Docker and hosting credentials unavailable. |
| 12. Portfolio | README, architecture, ER diagram, API/security/privacy/deployment/evaluation docs and CV walkthrough | Real screenshots and measured model evaluation pending. No hosted URL invented. |

## Environment

- Empty initial workspace; no existing code or Git repository.
- Node 24.22.1, Python 3.12.14 available through the bundled local runtime.
- Docker Desktop was installed after the initial checkpoint; Linux containers are now available.
- Package downloads require network-enabled execution. Installation uses only this project's virtual environment and cache.

## Deliberate limits

- No synthetic data displayed as real product records.
- PostgreSQL remains the application database. SQLite may only be used in isolated unit tests and is not an alternative application mode.
- No deployment, throughput, accuracy, fairness, or production-readiness claims without measured evidence.
