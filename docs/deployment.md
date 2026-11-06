# Deployment and environment

No hosting account, paid infrastructure or external deployment has been created. The provided deployment target is a Linux container environment with persistent PostgreSQL/pgvector, Redis and private files. Docker was not discovered in the initial Windows environment; see implementation status for validation performed later.

## Variables

| Variable | Purpose |
|---|---|
| DATABASE_URL / POSTGRES_PASSWORD | Matching credentials for API/worker and PostgreSQL; replace development values |
| REDIS_URL | Internal broker and shared throttle store |
| APP_ORIGIN | Exact browser origin, including scheme/port; required for mutation Origin checks |
| COOKIE_SECURE / ENVIRONMENT | Use true / production behind HTTPS; startup validates this |
| STORAGE_BACKEND | local or s3 |
| STORAGE_PATH | Private persistent volume, never frontend public/ |
| S3_BUCKET / S3_ENDPOINT_URL | Private production object store; empty endpoint uses AWS default |
| AWS credentials / region | Standard SDK environment/role chain, never public frontend variables |
| EMBEDDING_MODEL / EMBEDDING_REVISION | 384-dimensional model and immutable revision |
| SPACY_MODEL | Installed pretrained English pipeline |
| HF_HOME | Persistent model cache; Docker volume default |
| API_INTERNAL_URL | Next.js proxy destination; baked during frontend build, rebuild when changed |
| DEMO_MODE | Explicit isolated synthetic workspace banner and seeding guard |
| SEMANTIC_WEIGHT / SKILLS_WEIGHT / EXPERIENCE_WEIGHT / EDUCATION_WEIGHT | Nonnegative weights summing to 1; alter only with evaluation |

## Deployment procedure

1. Build images from reviewed source and lockfiles. Set production environment and secret-managed credentials. Use a dedicated DB role; an administrator enables pgvector once when the migration role lacks extension privileges.
2. Back up the database before migrations. Run a single `alembic upgrade head` release task. Do not run concurrent schema changes.
3. Mount private files and model cache, or configure verified private S3. Run one beat dispatcher and one CPU worker initially. Warm models and confirm they produce 384-dimensional vectors.
4. Start API and frontend behind HTTPS. Set exact origin, secure cookies, ingress request-size/time limits, trusted proxy rules and security headers. Publish frontend only; keep DB/Redis private.
5. Check liveness/readiness, perform real applicant/recruiter flows, inspect queue failures, confirm withdrawal/deletion, and download a PDF report. Health/readiness alone does not prove model readiness.
6. Monitor failed tasks, latency, outbox age, disk/memory use, backup recovery and database/storage access. Configure alerts through your hosting service.

The source can be adapted to a Vercel frontend with a container-hosted API/worker, but a same-origin proxy or carefully configured cookie domain/origin strategy is still required. No provider has been selected because pricing/capabilities were not validated for a real deployment. A small always-on container host is easier to reason about than a short-lived Python serverless runtime for these models.

## Rollback

Keep prior image tags and schema backups. Stop dispatching new jobs before a release rollback. Restore a compatible database snapshot when a schema downgrade would lose data; do not routinely execute destructive downgrades. Regenerate embeddings when model revisions change and reject mixed model vectors. Keep storage versions/retention aligned with database backups.

## Lightweight development

One CPU worker, batch size 16, no cross-encoder in live ranking, no approximate vector index. Run Next.js/API natively with DB/Redis in Docker if needed. SQLite is intentionally not offered as an application persistence substitute. Do not run native Windows Celery as a production service.
