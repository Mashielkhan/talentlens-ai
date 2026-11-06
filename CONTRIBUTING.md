# Contributing

Use Python 3.11/3.12, Node 22+ and PostgreSQL with pgvector. Follow README setup. Keep personal resumes, secrets, model caches and local databases out of Git.

Before a pull request, run Ruff, pytest, frontend lint/typecheck/unit tests/build. Use the full model/Playwright workflow when changing parsing, scoring, authorization or API contracts. State clearly which services/checks were unavailable. New schema changes require a new Alembic migration, not edits to a released migration. New scoring behavior requires a version change and reproducibility tests.

No fake model outputs or fabricated metrics. Synthetic fixtures must remain labeled. Every new recruiter data path needs an ownership/consent test. Preserve evidence and uncertainty; never add automatic rejection or demographic ranking. Do not upload real applicant data to issues, screenshots or public CI artifacts.
