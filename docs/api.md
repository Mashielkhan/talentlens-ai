# API contract

The authoritative generated schemas are available at `/docs` and `/openapi.json`. Prefix: `/api/v1`. List endpoints use bounded limits; resumes/jobs also support offset. API errors use `detail`; validation errors contain structured field diagnostics.

| Area | Implemented routes |
|---|---|
| Authentication | POST `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh`; GET `/auth/me`; PATCH `/auth/profile`; POST `/auth/password`; DELETE `/auth/account` |
| Resumes | POST/GET `/resumes`; GET/PATCH/DELETE `/resumes/{id}`; GET `/resumes/{id}/download`; POST `/resumes/{id}/reprocess` |
| Jobs | POST/GET `/jobs`; POST `/jobs/suggest`; GET/PATCH/DELETE `/jobs/{id}` |
| Applications | POST/GET `/jobs/{id}/applications`; GET `/applications`; PATCH/DELETE `/applications/{id}` |
| Matching | POST `/skill-gap/analyze`; POST `/jobs/{id}/match`; GET `/matches`, `/matches/{id}`; GET `/tasks/{id}` |
| Reports | GET `/reports/{id}/export`; GET `/reports/compare?ids=UUID&ids=UUID` |
| Analytics | GET `/analytics` (scoped to current role/ownership) |
| System | GET `/health`, `/ready` |

Mutations require an exact `Origin` matching `APP_ORIGIN`. Authenticated mutations additionally require `X-CSRF-Token` equal to the issued session token's CSRF value; the readable `tl_csrf` cookie supplies this. The opaque session credential is HttpOnly. API consumers must maintain a cookie jar. No bearer token is returned to JavaScript.

Upload/reprocess/analyze return 202, signifying queued work, not successful parsing. Resume state is returned by GET `/resumes/{id}`; matching task state by GET `/tasks/{id}`. Worker errors are explicit codes. Unsupported PDF scan pages return `OCR_REQUIRED_OR_EMPTY_PAGE`, not fabricated parsed text.

Job PATCH is a complete validated update of editable fields. Its version increments and existing matches are invalidated. Resume corrections accept contact fields, skills and supported sections; saving queues reprocessing and invalidates previous matches. Private analysis creates no application. An application requires `consent: true` and a completed owned resume.

Recruiter matching considers consented applications only. Match retrieval checks the current input versions; historical invalid matches return a conflict rather than an outdated score. Applicant-only analyses cannot be exported by recruiters. Candidate comparison requires two to four results for the same role, all accessible to the requester.
