# Troubleshooting

| Symptom | Check |
|---|---|
| `docker` not found | Install/start Docker Desktop and Linux/WSL2 support, reopen terminal |
| API ready returns 503 | PostgreSQL password/URL, `docker compose logs migrate`, vector extension, Redis health |
| Upload remains pending | Both worker **and beat** must be running; inspect their logs and task outbox |
| `PROCESSING_DEPENDENCY_ERROR` | Model download access, spaCy model installation, model-cache permissions, disk/memory; no fallback fake embeddings exist |
| `OCR_REQUIRED_OR_EMPTY_PAGE` | Supply a text-based PDF/DOCX, remove blank pages, or perform OCR externally |
| `NO_QUALIFICATION_SECTIONS` | Add conventional section headings or provide section corrections, then reprocess |
| `MIME_MISMATCH` | File extension, browser-provided MIME and content signature must agree |
| `DOCX_COMPRESSION_LIMIT` | Archive is suspicious or unusually compressed; export a fresh plain DOCX/PDF |
| 403 Origin/CSRF | Exact `APP_ORIGIN`, same-origin frontend proxy, current cookies and X-CSRF-Token; sign in again if expired |
| 429 after repeated testing | Shared Redis limits; wait the indicated window or use a fresh isolated test environment |
| Old report returns 409 | Resume/job changed. Run matching again. Old scores cannot be treated as current |
| Candidate absent | Check explicit consent, correct owned job, completed resume, current embeddings and top-100 retrieval cap |
| Deleted object still occupies disk | API access is revoked; worker deletion outbox must drain successfully |
| Frontend cannot reach API | Correct `API_INTERNAL_URL` at build time; rebuild Next.js after changing it |

For local Windows package installs, use Python 3.11/3.12 x64 in a virtual environment. Resolve dependency download failures before interpreting import failures as application bugs. The initial build used the bundled runtime and a project-local cache; ordinary user setup uses the commands in README.
