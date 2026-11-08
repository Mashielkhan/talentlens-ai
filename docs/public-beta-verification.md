# Applicant beta verification

Recorded November 8, 2026. Implementation follows `public-beta-plan.md`.

## Implemented

- Owner-only CV Studio drafts; job description stays private; source evidence and conservative wording suggestions; explicit saved-revision approval; PDF and editable DOCX exports.
- Source-version and revision conflicts prevent stale approval/export. Resume/account deletion cascades to drafts. Recruiter application consent never grants draft access.
- Hashed, expiring, single-use email tokens; SMTP TLS support; generic reset requests; session/reset-token revocation; configuration-aware account screens.
- Private feedback with per-user limits, email-verification gating, optional ClamAV streaming with fail-closed errors, production configuration validation, Caddy/Compose launch profile and preflight script.

## Executed checks

- Backend suite in Docker: 53 passed (49 unit/API, 3 PostgreSQL integration, 1 real-model test). The model test used the pinned model already cached locally.
- PostgreSQL migration 0002: passed on the isolated database and the existing local application database, with a private backup taken before the latter migration.
- Frontend Vitest: 6 passed, including approval invalidation and stale-source UI tests.
- TypeScript, ESLint and Ruff: passed.
- Production frontend build: passed during the Docker build.
- Production Compose configuration: parsed successfully using non-secret placeholder interpolation and no environment-file resolution.
- PDF export: parsed-content and pagination tests passed; a synthetic single-page CV was rendered with Poppler and visually inspected successfully.
- DOCX export: readable structure/content and download tests are included. Local visual rendering was attempted but could not run because LibreOffice/Word is absent; do not claim DOCX visual verification.
- Full Docker browser suite: 2 passed. The applicant/recruiter journey covers real resume processing and matching, consent, report download, draft creation, saved edits across reload, revision approval, PDF/DOCX downloads, approval invalidation after edits, feedback and deletion. The public-page check covers desktop and mobile.
- Browser testing caught prefilled textarea content being included in CV field labels. Explicit label associations fixed the issue; the complete journey then passed against the rebuilt production frontend.
- SMTP: a local socket-based mail sink received and decoded the recovery message correctly. This is transport coverage, not external inbox-delivery verification.
- Local application: latest backend/frontend images running successfully at `http://localhost:3001`; no public host was deployed.

## External launch dependencies

No public deployment, SMTP provider or domain has been connected. Real inbox delivery, actual ClamAV scanning/signature freshness, HTTPS on the eventual host, load limits and backup/restore must be verified before public launch. Unit mocks validate scanner protocol decisions and mail-token behavior; they do not establish actual provider delivery or malware-detection efficacy. The launch runbook lists free-first options and their constraints.

This is an English-focused beta. PDF export rejects unsupported glyphs with an explicit DOCX alternative. Guidance is conservative rules plus the existing skill taxonomy, not a generative writing model. No hiring-validity or fairness claims follow from the synthetic tests.
