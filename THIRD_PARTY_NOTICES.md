# Third-party notices and technical references

TalentLens AI — Copyright (C) 2026 Mashiel Khan. The original TalentLens source uses AGPL-3.0-or-later; the complete license is included in LICENSE. Dependencies/models retain their respective licenses; inspect installed versions before redistribution.

- [all-MiniLM-L6-v2 model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2): Apache-2.0; 384-dimensional sentence embeddings. Model revision is recorded in results.
- [PyMuPDF license](https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright): AGPL/commercial dual licensing. This repository does not assume that an MIT license alone covers the PDF-processing dependency.
- [spaCy documentation](https://spacy.io/usage): pretrained pipelines are separate packages; general NER is not resume-domain training.
- [Sentence Transformers API](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html): CPU/device configuration, revision selection and normalized encoding.
- [pgvector](https://github.com/pgvector/pgvector): exact cosine distance retrieval and PostgreSQL vector storage.
- [Next.js installation](https://nextjs.org/docs/app/getting-started/installation): Node compatibility; lint runs separately from production builds.
- [Celery tasks](https://docs.celeryq.dev/en/stable/userguide/tasks.html): idempotency, acknowledgements and process time limits.
- [OWASP file uploads](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): layered upload validation and private storage guidance.

The skill catalog and fictional documents are original project fixtures. No ESCO/O*NET data is redistributed. shadcn-style source components depend on Radix/CVA and follow the component-source pattern; they are not proprietary UI assets.
