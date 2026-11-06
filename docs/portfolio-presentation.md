# Portfolio presentation — Mashiel Khan

## Project description

TalentLens AI is a full-stack qualification-analysis application combining private document processing, NLP skill extraction, semantic embeddings and explainable job matching. It connects applicant and recruiter workflows through explicit application consent and evidence-based reports.

## CV bullets

- Implemented a Next.js and FastAPI resume-analysis platform with role-based access, private PDF/DOCX processing, editable qualification profiles, consented applications and downloadable reports backed by PostgreSQL/pgvector and Celery.
- Designed a CPU-based NLP and hybrid-matching pipeline using spaCy, Sentence Transformers, weighted skill coverage and overlap-aware experience analysis, with inspectable evidence, uncertainty handling and automated authorization/scoring tests.

Use these after reviewing actual validation status. Do not add production-user counts, accuracy, throughput or deployment claims unless measured and documented.

## Interview walkthrough

1. Explain the problem: differently formatted resumes obscure qualification evidence; keyword counts alone miss contextual relevance.
2. Show privacy boundaries: upload is private; private matching does not share; application consent grants one job's recruiter access; withdrawal revokes it.
3. Trace the pipeline: file validation and private storage → durable task → document parser → spaCy/regex/PhraseMatcher → structured evidence → section chunks → normalized embeddings → PostgreSQL vectors.
4. Walk through hybrid scoring with a real report. Explain required vs preferred, overlap union, omitted unknown components, effective weights and why the score is not a probability.
5. Show a correction invalidating previous analysis, then recompute. Explain model revisions and task idempotency.
6. Discuss tests and tradeoffs honestly: isolated authorization tests versus PostgreSQL/model integration, limited synthetic labels, general NER, layout and fairness risks.
7. Explain the next engineering work: independent annotated evaluation, more structured extraction, deployment validation, scaling measurements, and only then optional reranking.

## Suggested screenshots

- Landing page and empty applicant dashboard (no fake activity).
- Actual completed synthetic resume with skill evidence and editable sections.
- Recruiter-confirmed required/preferred criteria.
- Real analysis breakdown showing uncertainty and adjusted weights.
- Two-candidate authorized comparison and downloaded PDF.
- Passing test output and measured evaluation results, with the synthetic scope label visible.

The product should be demonstrated with isolated synthetic data, not personal resumes. Capture images from the running system; do not present UI mockups as verified inference output.
