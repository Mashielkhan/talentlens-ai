# Database schema

UUID primary keys, timestamps, cascading foreign keys, unique emails, unique applicant/job applications, JSONB parser evidence, and vector(384) section embeddings are implemented in SQLAlchemy and the fixed Alembic `0001` migration. Changing live model definitions does not silently change old migrations.

```mermaid
erDiagram
  users ||--o{ sessions : authenticates
  users ||--o{ resumes : owns
  users ||--o{ jobs : creates
  users ||--o{ applications : submits
  users ||--o{ audit_logs : acts
  resumes ||--o{ resume_sections : embeds
  jobs ||--o{ job_sections : embeds
  jobs ||--o{ applications : receives
  resumes ||--o{ applications : shares
  applications ||--o{ match_results : permits
  resumes ||--o{ match_results : describes
  jobs ||--o{ match_results : targets
  resumes ||--o{ processing_tasks : processes
  jobs ||--o{ processing_tasks : ranks
  users {
    uuid id PK
    string email UK
    string password_hash
    string role
    jsonb profile
  }
  resumes {
    uuid id PK
    uuid owner_id FK
    string storage_key UK
    string file_hash
    int version
    jsonb parsed_data
    jsonb corrections
  }
  resume_sections {
    uuid id PK
    uuid resume_id FK
    string section_type
    vector embedding
    string model_version
  }
  applications {
    uuid id PK
    uuid job_id FK
    uuid applicant_id FK
    uuid resume_id FK
    timestamp consent_at
  }
  match_results {
    uuid id PK
    uuid application_id FK
    uuid requester_id FK
    int resume_version
    int job_version
    float score
    jsonb result
  }
```

`storage_deletions` intentionally has no owner/resume FK so deletion work survives account erasure. Audit actor IDs become null when accounts are deleted. Records never contain passwords or extracted document bodies in audit actions.

Indexes cover ownership/filter relationships and job status. Job full-text search has an English GIN expression index. Vector search is exact; no HNSW/IVFFlat index is claimed to improve an unmeasured workload. The application does not support SQLite; tests use SQLite variants solely to isolate authorization/business logic.

Initial simplifications: applicant/recruiter profile attributes use `users.profile`; normalized skill vocabulary is an original versioned Python catalog; extracted skills, employment, education, projects and certifications remain evidence-bearing JSONB/narrative fields. They are not all represented as fully normalized independent tables. See limitations before presenting the schema as the complete aspirational master brief.
