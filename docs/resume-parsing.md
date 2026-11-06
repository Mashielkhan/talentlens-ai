# Resume parsing

Pipeline: bounded upload → extension/MIME/signature validation → private UUID object → worker text extraction → section detection → spaCy general NER + regex contacts + PhraseMatcher skills → date intervals → correction merge → qualification-only embeddings → database persistence.

PDFs use PyMuPDF's sorted text extraction and a 30-page cap. Encrypted, malformed, empty, or potentially scanned pages are explicitly rejected. A document with a blank page can conservatively trigger the OCR flag; remove blank pages or supply DOCX. Multi-column text is extracted but reading order is not guaranteed. No OCR engine is installed.

DOCX uses python-docx body iteration, tables, and headers. ZIP member count, uncompressed size, compression ratio, embedded binaries/macros, and XML entity declarations are checked. Resource limits are also enforced at the Celery process boundary. Documents are never executed. This does not replace a production malware scanner.

Recognized sections include summary/profile/objective, skills/technical expertise, experience/employment, education/academic background, projects, and certifications. Text preceding a recognized heading is treated as contact data and excluded from embeddings. If no sections are recognized, the user must provide section corrections; the worker does not invent a profile.

General pretrained spaCy entities are PERSON/ORG/GPE/DATE. Default spaCy does not directly identify every job title, degree, certification or institution. Emails, selected social links, phone patterns and employment ranges use deterministic rules. Education/projects/certifications preserve narrative section evidence rather than claiming a fully solved structured extraction task. Names are taken only from a plausible leading PERSON entity; missing values remain empty.

Date patterns support English month/year and year-only ranges. Year-only values conservatively use January and flag approximation. Current roles end at the parsing date. Duration uses half-open month intervals and unions overlaps; incomplete/ambiguous dates remain unknown. Relevant experience requires required-skill evidence in the dated entry. This is an engineering heuristic, not verified employment history.

Corrections remain separate from raw text. Applicant-confirmed skills are visibly labeled as such; neither source text nor corrections establish proficiency. Model inputs exclude contact sections, email/URL patterns, explicit demographic lines and recognized person/place entities. Proxies and NER errors remain possible.
