# Known limitations and remaining work

- This is a substantial first implementation, not completion of every aspirational phase in the master brief. Executed checks are listed separately in implementation-status.md.
- No cloud deployment, paid hosting selection, or independent production security audit.
- No automatic OCR. Mixed scanned/blank PDFs conservatively fail with a visible OCR message.
- English rule-based sections and general spaCy NER. No custom trained resume entity recognizer; company/title/institution/degree/project/certification fields are not all reliably normalized into separate relational tables.
- Header/body parsing supports common layouts, not arbitrary resume design. DOCX footers, embedded text boxes, multi-column reading order and multilingual formats need expanded evaluation.
- Curated IT taxonomy is deliberately small. Ambiguous abbreviations, negation, nested skill names and custom terms may need correction.
- Month/year extraction and lexical education equivalence are conservative. Unknown components are omitted; compare coverage/uncertainty alongside scores.
- Protected data exclusion is best effort. No independently measured fairness or validity for employment decisions. Never automate rejection.
- Exact vector retrieval uses the first job chunk for a top-100 shortlist; full hybrid scoring uses all stored chunks. Large-pool retrieval performance is not benchmarked.
- Cross-encoder is available only in offline evaluation, not promoted to live ranking without evidence.
- No email verification/password reset delivery provider configured. No public read-only demo isolation layer. Local synthetic demo accounts are writable.
- S3 needs credentials, bucket policy and integration validation. No antivirus/CDR integration. Worker hard resource constraints and ingress controls require deployment validation.
- Lists have bounded limits; frontend pagination for datasets beyond those initial limits remains to be added. Analytics use application queries and should be optimized for larger datasets.
- Task progress is coarse queue/processing/completed state, not a fine-grained percent estimate. Automatic retry is bounded; API UI supports explicit reprocessing.
- No 100/1,000-resume performance claims, screenshots of invented scores, or fabricated evaluation metrics.
