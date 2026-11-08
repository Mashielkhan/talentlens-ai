# Implementation status

**November 8 applicant-beta work:** see [public-beta-verification.md](public-beta-verification.md) for the new CV Studio, account access and deployment checks. The November 6 checkpoint below is retained as historical validation.

This file distinguishes implemented source from executed verification. Checkpoint recorded on November 6, 2026. The owner authorized continued Docker integration validation and public GitHub publication after the unit-test checkpoint.

## Review checkpoint

| Executed check | Result |
|---|---|
| Backend unit/API + PostgreSQL integration tests | **37 passed**, 1 real-model test deliberately deselected; 6.14 seconds locally |
| Frontend Vitest tests | **4 passed** in 2 test files |
| Ruff (`backend scripts ml`) | Passed |
| ESLint | Passed with no remaining warnings/errors |
| TypeScript `tsc --noEmit` | Passed |
| Next.js production build (`next build --webpack`) | Passed; 12 static pages generated and dynamic detail routes compiled |
| Python source compilation | Passed |
| PostgreSQL 17 / pgvector migration, consent/model filtering, deletion cascades | Passed locally in Docker and on GitHub CI |
| Redis container readiness | Passed (`PONG`) |
| Public-page Playwright browser smoke test | Passed on GitHub CI |
| GitHub quality workflow | Passed after upgrading vulnerable setuptools build tooling |
| Pinned spaCy / MiniLM model warm-up and real inference test | Passed in the full GitHub workflow; 384-dimensional embeddings; 1 model test passed |
| Full Docker applicant/recruiter browser journey | Passed; both Playwright tests passed in 30.3 seconds |
| Local Docker browser journey | Both Playwright tests passed in 1.2 minutes using installed Chrome at localhost:3001 |
| Synthetic evaluation | Executed; measured JSON/CSV saved under `ml/results/`; see `model-evaluation.md` for scope and limitations |

Executed workflow records: [quality checks](https://github.com/Mashielkhan/talentlens-ai/actions/runs/42210546607) and [full Docker/model/journey validation](https://github.com/Mashielkhan/talentlens-ai/actions/runs/42210731731). Combined backend coverage is 38 tests; the model check runs separately from the other 37.

The 34 unit/API-isolation tests use an in-memory SQLite fixture and replace Redis throttling. Three additional tests execute against migrated PostgreSQL/pgvector, checking vector queries, full-text search, consent and model filtering, and deletion cascades. The vector-filtering test uses controlled vectors to verify SQL isolation, not inference quality. The full Docker journey executes Celery processing and pretrained spaCy/MiniLM inference through the browser. The dependency auditor cannot map the local application or PyTorch's CPU-specific version to PyPI; those skips are visible in CI logs.

The test run found and fixed nested skill alias duplication: `React JS` no longer separately asserts JavaScript, and `Postgre SQL` no longer separately asserts SQL. The matcher now selects the longest non-overlapping phrases. Python/frontend formatting and import lint issues were fixed without weakening test assertions.

### Environment issues encountered

- Pytest's default temporary directory was not writable in the sandbox; final verification used a dedicated workspace-local temp directory.
- Windows asyncio's internal loopback socket pair hung in the network sandbox. The final backend suite ran with approved execution outside that sandbox; the diagnostic trace located the hang before API test startup.
- The default Turbopack build failed spawning its CSS subprocess. A sandboxed Webpack build also hit generated-directory permissions. The approved Webpack build outside the sandbox completed successfully.
- Initial local browser attempts could not reach the sandboxed server. The public-page browser smoke test subsequently passed on GitHub CI; the authenticated full journey is tracked separately.
- The native test environment includes Python 3.12.14, FastAPI 0.162.0, SQLAlchemy 2.0.57, pytest 9.2.0, spaCy 3.8.18, PyMuPDF 1.28.2 and ReportLab 4.5.1. Docker installs the full dependency set. A Starlette warning notes future deprecation of its httpx test-client adapter; it did not fail any test.

### Integration checkpoint

Docker Desktop is installed, with healthy PostgreSQL/pgvector and Redis containers. The local application and both browser tests pass at http://localhost:3001, with the pinned model cached in a persistent volume. Port 3000 was occupied by an existing process, so the ignored local `.env` uses port/origin 3001. The default shared configuration remains port 3000. Long downloads required persistent build caches and longer timeouts. The full GitHub Docker/model/browser workflow passed. The public source repository is https://github.com/Mashielkhan/talentlens-ai; no hosted application is deployed.

| Phase | Source status | Verification / remaining work |
|---|---|---|
| 1. Setup | Next.js, FastAPI, PostgreSQL/pgvector, Redis/Celery, Compose, health/readiness | Frontend build, database migration and backend tests passed. PostgreSQL and Redis containers healthy. |
| 2. Authentication | Argon2, opaque server-side sessions, CSRF, role/object authorization, settings/deletion | API-isolation authorization tests passed. No email recovery provider. |
| 3. Documents | Private local/S3 storage, bounded PDF/DOCX validation, extraction, corrections, reprocessing | Document parsing/safety tests passed. S3 not tested. OCR explicitly unsupported. |
| 4. NLP | spaCy NER, PhraseMatcher taxonomy, sections, contact regex, dated experience with overlap union | Real model inference passed. Structured employment/education fields remain heuristic; broader evaluation pending. |
| 5. Jobs | Draft/publish/archive, requirements review, weighted skills, application consent and withdrawal | Full browser journey passed with actual API, database and worker. |
| 6. Matching | Pinned MiniLM model, token-aware chunks, vector persistence and authorized exact retrieval, hybrid scoring | Real model consistency test and private/recruiter browser matching passed. |
| 7. Explainability | Effective weights, evidence, uncertainty, deterministic gaps/resources, private PDF exports | Scoring and PDF content/pagination tests passed. Human visual report review pending. |
| 8. Advanced retrieval | Exact pgvector shortlist of 100; optional offline cross-encoder experiment runner | Synthetic keyword/semantic/hybrid evaluation executed. Cross-encoder and scale benchmarks remain unexecuted. |
| 9. UI | Landing, auth, dashboards, resume/profile editing, jobs, matching, comparison, analytics, settings | Unit tests, lint, TypeScript, production builds and two browser tests passed. |
| 10. Testing | Integration checkpoint reached | 38 backend + 4 frontend unit tests and 2 browser tests passed across workflows. |
| 11. Deployment | Compose and Dockerfiles; public GitHub repository | Full Docker validation passed on GitHub. No hosted application deployed. |
| 12. Portfolio | README, architecture, ER diagram, API/security/privacy/deployment/evaluation docs and CV walkthrough | Measured synthetic evaluation included; portfolio screenshots remain optional follow-up. No hosted URL invented. |

## Environment

- Empty initial workspace; no existing code or Git repository.
- Node 24.22.1, Python 3.12.14 available through the bundled local runtime.
- Docker Desktop was installed after the initial checkpoint; Linux containers are now available.
- Package downloads require network-enabled execution. Installation uses only this project's virtual environment and cache.

## Deliberate limits

- No synthetic data displayed as real product records.
- PostgreSQL remains the application database. SQLite may only be used in isolated unit tests and is not an alternative application mode.
- No deployment, throughput, accuracy, fairness, or production-readiness claims without measured evidence.
