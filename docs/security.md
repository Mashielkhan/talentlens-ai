# Security boundaries

Implemented: Argon2 password hashing; random opaque 24-hour session credentials stored only as SHA-256 hashes; HttpOnly session cookie; SameSite=Lax; secure cookies required in production; server-side session revocation; exact Origin and per-session CSRF checks on mutations; bounded typed inputs; ORM queries; role and object checks; no public resume pool; private uploads; Redis-backed account/IP upload/login throttles; safe error codes; structured logs without resume text; audit actions; download authorization; cascading data removal and durable file-deletion outbox.

Account role is selected only from APPLICANT/RECRUITER at registration; ADMIN cannot be self-assigned. Recruiter resume access requires a live application to an owned job. Guessing a UUID does not grant access. Private applicant analyses stay private. Invalidated results cannot be exported as current.

PDF/DOCX processing is limited to 10 MB, 30 PDF pages and 150,000 extracted characters. DOCX checks archive expansion, member count, macros/embedded content and XML entity declarations. API also checks declared and streamed request sizes; production ingress must cap bodies and request time. Worker task time limits and one-process concurrency reduce resource exposure. Uploaded objects use random keys; original names are display-only.

Remaining production work: deployment threat review; independent penetration testing; malware scanning/content disarm where needed; outbound worker network restrictions; CSP tuned for the hosted Next.js app; password recovery with expiring single-use tokens and a verified email provider; email verification; infrastructure secret rotation, backup encryption and retention; monitoring and incident response. Login throttling must use trusted proxy configuration, never arbitrary client-supplied forwarding headers.

S3 support is implemented but requires bucket policy/block-public-access validation and a live integration test. Only API-side reads are used; no public URL is emitted. Configure least-privilege IAM and encrypted transport. Avoid exposing Docker ports beyond loopback in development.

Dependency audit commands and CI checks are included. Passing lint/tests is not proof of security. Consult the execution record for which audits actually ran.
