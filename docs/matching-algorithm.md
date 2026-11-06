# Explainable matching

Model: `sentence-transformers/all-MiniLM-L6-v2`; immutable revision configured through environment. 384 dimensions, normalized embeddings, CPU inference, batch size 16, overlapping token chunks up to 240 tokens (or model limit minus two, whichever is smaller), overlap 32. Model mismatch requires regenerating sections; dimension changes require a database migration.

Candidate qualification sections exclude contact data. Job input contains description and reviewed required/preferred skills, excluding separate company/location fields. Exact pgvector cosine distance to the first job chunk retrieves up to 100 consented completed applicants; all job chunks contribute to the final semantic score. This shortlist approximation is explicit: candidates outside it do not receive a ranking in that run.

For each job chunk, take maximum cosine similarity across resume chunks. Clamp to [0,1], average across job chunks and multiply by 100. This is an engineering relevance signal, not calibrated probability. Long or repeated job descriptions can change relative chunk influence.

Required skills: `100 * matched_required_weight / all_required_weight`. Preferred gaps are explained separately and preferred text contributes to semantics. No required criteria means this component is not applicable.

Experience: union the dated intervals whose evidence includes a required skill. Score is `min(100, documented_relevant_months / required_months * 100)`. Unknown relevant intervals or unspecified requirements omit the component. Approximate year-only dates are flagged. This can undercount genuine experience and must not disqualify an applicant automatically.

Education: if all requirement terms are present as whole words in the education section, documented phrase evidence scores 100. Otherwise education remains unknown and omitted; the system does not infer degree equivalence or claim a person lacks education.

Defaults: semantic .45, required skills .30, experience .15, education .10. All values are 0–100. Omitted components redistribute their weights proportionally. Effective weights, evidence, uncertainties, missing requirements and original heuristic disclaimer accompany each result. Unknown information can therefore yield a relatively high score with limited evidence: inspect component availability, never use the number as an automatic filter.

Results store document/job versions, model revision, scoring-config fingerprint, calculation timestamp and experience as-of date. A document/job edit invalidates prior results. Manual corrections are labeled. No random scoring, opaque LLM verdict, automated rejection or hire probability exists.

Cross-encoder reranking is an **offline experiment only** through `ml/evaluation/evaluate.py`. It reranks the top ten hybrid candidates and records latency/quality. It is not promoted into production ranking without comparison on a useful held-out dataset.
