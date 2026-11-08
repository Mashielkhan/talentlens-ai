# Public beta implementation plan

## Goal and scope

Deliver an applicant-focused beta: upload a CV, create a private tailored draft from a pasted job description, review evidence-based editing suggestions, edit and approve the exact revision, and download a usable PDF or DOCX. Preserve the existing applicant/recruiter matching workflow.

This plan is written before implementation. Hosting, domain and email-provider configuration are external dependencies; no paid infrastructure will be purchased without authorization. Source readiness and an actually deployed public service will be reported separately.

## Implementation order

1. **CV Studio:** persisted owner-only drafts, original evidence alongside suggestions, job-skill guidance, editable sections/contact details, explicit factual-review approval, PDF/DOCX export, revision conflict detection and source-version invalidation. Suggested wording must preserve documented facts; no fabricated metrics, employers or qualifications. The first beta uses conservative editing rules alongside the app's existing NLP matching, with no undisclosed external sharing of CVs.
2. **Account recovery and beta support:** expiring single-use hashed email tokens, verification/resend and password reset, revocation of sessions on reset, configurable SMTP delivery, clear configuration-aware UI, and private feedback submission with abuse limits.
3. **Public deployment safeguards:** enforce verified accounts for expensive actions when enabled, bounded draft/feedback creation, optional ClamAV scanning that fails closed when configured, production configuration checks, HTTPS reverse-proxy deployment configuration, and documented backup/restore and launch steps. Preserve private uploads and consent boundaries.
4. **Validation:** migration and unit/API tests for ownership, stale revisions, approval/export, token expiration/reuse, session revocation and scanner failure; inspect generated PDF/DOCX output; run lint, TypeScript, frontend unit tests, production build, and real Docker browser journeys covering existing features plus CV Studio.
5. **Checkpoint:** publish tested changes to the existing public repository, update actual verification results and remaining deployment dependencies, then stop for review.

## Acceptance criteria

- A signed-in applicant can save, revisit, edit, approve and export a private CV draft using a pasted job description without creating a recruiter job.
- Every proposed replacement shows its original source text and requires a user action; missing skills are guidance, never silently inserted as qualifications.
- Export requires approval of the current revision. Editing or changing the underlying resume invalidates that approval. Another user or recruiter cannot read/export a draft, including through an existing application.
- Password recovery and verification tokens expire, cannot be reused, are not exposed in responses/logs, and cannot be used for another purpose. Reset requests use generic responses.
- New migrations preserve existing data. Account/resume deletion cascades to drafts and account tokens.
- Existing matching, consent, reporting and deletion journeys continue to pass.
- A public URL is only reported after a real deployment and smoke test; unavailable hosting/email/scanning credentials are recorded explicitly.

Checkpoint reached November 8, 2026: the implementation and local automated checks are complete. See `public-beta-verification.md` for results and `public-beta-launch.md` for external launch dependencies. Further feature work and public hosting setup await owner review.

## Deferred beyond this beta

Paid subscriptions, a scraped/live job marketplace, multilingual OCR, custom model training, production cross-encoder ranking, independent fairness studies and broad real-resume validation. Current synthetic metrics are not hiring-validity evidence.
