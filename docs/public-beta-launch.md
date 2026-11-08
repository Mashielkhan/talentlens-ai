# Public beta launch runbook

## Current boundary

The beta source supports private CV drafting, explicit review, PDF/DOCX export, email verification/recovery and feedback. No external host, mailbox provider or domain has been connected. A local Docker address is not a public deployment. Do not announce public availability until the checks below pass on the actual host.

## Free-first hosting decision

This application needs a Next.js process, a Python API, a model worker, Redis, PostgreSQL/pgvector, private persistent files and a scanner. A frontend-only free deployment cannot provide the full workflow. Free hosting eligibility and resource limits must be checked at signup; do not enter billing details or upgrade without the owner's approval.

Provider documentation checked during planning:

- [Render free-service limits](https://render.com/docs/free): evaluate memory, sleeping services, persistent storage and worker availability before selecting a plan. A free frontend alone is insufficient.
- [Hugging Face Spaces](https://huggingface.co/docs/hub/main/en/spaces-overview): current documentation says new Docker/Gradio compute Spaces require a paid plan even though CPU Basic has no hourly charge. Do not promise this as a free full-stack host.
- [Oracle Always Free resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm): as checked November 8, 2026, the A1 allowance is equivalent to 2 ARM OCPUs and 12 GB memory, subject to account eligibility and regional capacity. This is a candidate for the complete stack, not a verified deployment; ARM image/model compatibility must be tested on the actual VM. [Signup](https://docs.oracle.com/en/learn/cloud_free_tier/) normally requires the owner’s phone and card verification. Stay within the account’s Always Free allowance and do not upgrade to paid service without approval. Idle instances may be reclaimed.

The practical deployment artifact is a Linux Docker Compose stack that can run on an owner-provided eligible free VM or an approved paid VM. Minimum resources must be established under load; the model worker and ClamAV are each capped at 2 GiB in the supplied profile. Availability of a genuinely free suitable VM is not guaranteed. Account signup, email/domain verification and any card verification must be completed by the owner.

## Configure and launch

1. Provision a Linux host with Docker Compose >=2.24.4, sufficient memory and persistent disk. Point a hostname to it. Allow only SSH as appropriate and public ports 80/443; never expose PostgreSQL, Redis or ClamAV.
2. Clone the public repository, copy `.env.example` to the ignored `.env.beta`, replace the database password **in both variables**, and configure `PUBLIC_ORIGIN=https://your-hostname` and `SITE_DOMAIN=your-hostname`. Keep `DATABASE_URL`/`REDIS_URL` pointed at internal `db`/`redis` services.
3. Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_FROM` and `SMTP_SECURITY=starttls` (or `ssl`). Verify the sender/domain with your chosen provider. Never put these values into Git or chat. Production mode requires SMTP, verification, secure cookies and ClamAV scanning.
4. Validate and start:

   ```sh
   docker compose --env-file .env.beta -f compose.yaml -f compose.beta.yaml config --quiet
   docker compose --env-file .env.beta -f compose.yaml -f compose.beta.yaml up -d --build
   docker compose --env-file .env.beta -f compose.yaml -f compose.beta.yaml exec worker python -m scripts.warm_models
   docker compose --env-file .env.beta -f compose.yaml -f compose.beta.yaml exec api python -m scripts.beta_preflight
   ```

5. Wait for ClamAV signature initialization. Scanning fails closed until it is available. Confirm clean-file acceptance and EICAR rejection in an isolated check, and monitor signature freshness.
6. Register a fresh account in the browser. Verify actual email delivery and token expiry/reuse, upload a synthetic resume, create/edit/approve/export a draft, reset the password and confirm prior sessions stop working. Check existing job/application matching. Do not use real applicant files for deployment smoke tests.

Caddy terminates HTTPS and routes `/api/*` directly to the internal API. Only the isolated proxy network may reach the API; the production API trusts forwarded client-IP headers from that network. This preserves per-client throttling. Do not publish the API port or connect untrusted containers to that network.

## Operations and release gates

- Email links are delivered as background tasks in the API process; delivery failures are logged without recipients or tokens. The user can resend. This first beta does not provide a durable email outbox or delivery guarantees. Monitor `account_mail_delivery_failed` and test inbox delivery before launch.
- Back up PostgreSQL with `pg_dump -Fc` using the deployment's secret environment. Back up private resume storage separately; never publish backup files. Test restoration into a separate database and storage namespace, including a resume download and consent checks. Define and publish backup retention before accepting public personal data.
- Monitor HTTP failures, model-task failures, queue age, disk use, resource pressure and ClamAV freshness. Preflight is a startup check, not continuous monitoring.
- Review feedback privately through an authenticated operator database session; no public feedback-list endpoint exists. Account deletion removes feedback and drafts along with other account data.
- Pin deployment images/dependencies to reviewed versions for repeatability. Take backups before migrations. Keep the previous image and a compatible database restore plan; never roll back by deleting production volumes.
- The single-column PDF supports common Latin text. DOCX is editable; review complex scripts and long documents manually. The editor cannot verify user-entered facts. Existing matching scores remain heuristic.

Launch blockers: no suitable host selected, no verified email sender, no actual public-host scan/TLS/load/backup-restore verification. These are distinct from passing local automated tests.
