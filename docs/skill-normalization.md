# Skill normalization

`backend/app/nlp/taxonomy.py` is an original curated software/IT catalog across languages, web, backend, databases, AI/ML, cloud, DevOps, security, data, mobile, testing and professional competencies. It is not an ESCO/O*NET import or a comprehensive labor-market ontology.

spaCy PhraseMatcher uses token-aware, case-insensitive phrases. Aliases normalize ReactJS/React.js/React JS → React, Postgres/Postgre SQL → PostgreSQL, JS → JavaScript, NodeJS → Node.js. C++, C#, and .NET are preserved. Repeated aliases consolidate into one canonical skill with the first observed section evidence.

Bare Go and R require a skills-section context or explicit language/programming context. This reduces, but cannot eliminate, ambiguity. Negation, aspirational skills, nested names such as React Native/React and very short abbreviations require evaluation and review. No mention is interpreted as mastery.

Job inputs normalize aliases, reject duplicates across required/preferred lists, and validate weights in (0,5]. User corrections also normalize names. Unrecognized custom skills are allowed as explicit criteria but require manual evidence correction; the phrase catalog does not automatically recognize arbitrary custom terms.

Learning resources are explicitly maintained official documentation links. Missing catalog entries receive a practical evidence-building action without a fabricated link or certificate recommendation.
