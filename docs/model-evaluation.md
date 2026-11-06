# Evaluation scope

No independently validated accuracy, fairness, latency or throughput is claimed. Check `implementation-status.md` for actual execution results and `ml/results/` for files produced by runs, if any.

## Executed synthetic sanity run — November 6, 2026

[Measured JSON](../ml/results/synthetic-evaluation.json) and [per-pair rankings](../ml/results/synthetic-rankings.csv) record a local Docker CPU run using the pinned MiniLM model. This runner analyzes the fixture source text; document extraction is checked separately by document tests and the browser journey.

On the 20 developer-authored texts, skill precision/recall/F1 and exact email extraction were each 1.0. Mean nDCG@3 over five roles was 0.9480 for keywords, 0.9763 for semantic similarity and 1.0000 for hybrid scoring. Every method achieved Precision@3 of 0.6667, Recall@3 of 1.0 and MRR of 1.0; each role has only two grade-2-or-higher examples. Parsing took 10.59 seconds and embedding took 24.06 seconds in this run, including initialization and under concurrent local build activity. These timings are not a controlled performance benchmark. No cross-encoder was executed.

The deliberately simple texts closely match the taxonomy and role descriptions. Perfect scores on this corpus do not establish generalization, fairness, or improvement on real resumes.

The generator creates 20 original fictional documents in five software domains, four qualification tiers per domain, paired PDF/DOCX variants, five jobs and explicit relevance grades (0–3). Gold skill sets and exact emails are assigned at creation. This small developer-authored corpus is a regression/sanity dataset and can favor the rule system. It is not a substitute for held-out real resumes with independently adjudicated annotations.

`python ml/evaluation/evaluate.py` executes spaCy and the pinned Sentence Transformer. It reports micro skill precision/recall/F1, exact email accuracy, actual parsing and embedding elapsed time, and job-level Precision@3, Recall@3, MRR and nDCG@3. A relevant document is grade >=2. Ranking compares skills-only, semantic-only, full hybrid, semantic+skills, and semantic+skills+experience. Outputs include model/platform identifiers, CSV score rows and JSON metrics.

Optional cross-encoder evaluation requires both model ID and immutable revision. It reranks only the top ten hybrid results and measures incremental latency. Passage ranking weights are not assumed appropriate for recruitment.

Unit tests cover skill aliases/boundaries, uncertainty, experience overlap, dates, deterministic scores, input updates and removal of explicit contact/demographic lines. Real-model tests compare a backend vs frontend resume on a backend role. These are useful consistency checks, **not a broad fairness audit**. Name/gender/proxy perturbation suites, multi-language evaluation, field-level institution/title metrics, and 100/1,000-candidate database retrieval benchmarks remain necessary before claims at those scales.

Do not tune and report on the same tiny corpus as if held-out. A next evaluation should separate train/development/test documents, use multi-annotator relevance labels, include extraction failure examples, and report both retrieval metrics and human-review impact.
