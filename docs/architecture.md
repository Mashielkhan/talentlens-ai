# Architecture and design decisions

The browser uses a same-origin Next.js rewrite to `/api/v1`. FastAPI owns authorization and business rules. PostgreSQL owns durable state and 384-dimensional pgvector embeddings. Redis holds short-lived throttling counters and Celery messages. Private files are read only through authorized API endpoints.

`app/api` validates requests and selects permitted resources. `repositories/access.py` centralizes ownership/consent boundaries. `services/processing.py` coordinates reusable `nlp` and `ml` components. The frontend never calculates ranking scores.

Uploading writes an object then creates a resume and task in one database transaction; a failed database operation compensates by deleting the object. API task publication does not depend on Redis being available at that instant. A single beat dispatcher periodically reads pending tasks and publishes IDs. Duplicate messages are expected: a per-task PostgreSQL advisory lock and terminal-state check prevent duplicate processing. Failed dependencies retry up to three times. A processing lease older than 12 minutes can be redispatched after worker failure. Worker soft/hard limits are 9/10 minutes.

Expensive inference happens in the worker. It reloads and locks the resume before saving, then checks input version to avoid overwriting a newer correction. Job matching locks the job and rechecks requirements. Resume/job edits invalidate previous matches. Each result contains pinned model and scoring identifiers. The first 100 authorized candidates are retrieved with exact pgvector distance before hybrid scoring; a large pool is not exhaustively reranked.

Deletion removes relational access immediately and writes a durable storage-deletion outbox record. The worker deletes the file independently; transient storage errors can be retried without resurrecting the resume. Backups and previously downloaded copies have separate retention semantics.

Baseline inference is CPU-only with one worker process. The pretrained spaCy pipeline and Sentence Transformer are cached in process, and model files are persisted across container restarts. Horizontal scaling needs shared S3-compatible storage, a shared database/Redis, and a single beat scheduler. No separate vector database is required.

The default deployment uses one Python image for API/worker to simplify reproducibility; API processes do not load embedding weights. Profile and domain extraction are kept in bounded JSONB with evidence, while jobs, applications, sections, matches, tasks, sessions and audits are relational. Domain normalization can be expanded through subsequent migrations after extraction quality improves.
