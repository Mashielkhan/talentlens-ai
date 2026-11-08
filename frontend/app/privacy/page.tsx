import Link from "next/link";
import { Brand } from "@/components/common";
export default function PrivacyPage() {
  return (
    <main className="content max-w-3xl mx-auto">
      <Brand />
      <article className="panel stack mt-8">
        <h1>Beta privacy and use</h1>
        <p>
          TalentLens stores your account details, uploaded resumes, extracted profiles, private CV drafts,
          analyses and feedback to provide the service. Verification and recovery messages use the email
          service configured by the operator.
        </p>
        <h2>You control sharing</h2>
        <p>
          Uploading, analyzing or editing a CV does not share it with recruiters. Applying to a job shares the
          selected uploaded resume with that job’s recruiter. CV Studio drafts remain private. Downloaded
          copies may remain with their recipients after you withdraw.
        </p>
        <h2>Review and deletion</h2>
        <p>
          You can correct extraction, delete resumes and drafts, withdraw applications and delete your account
          in Settings. File deletion is processed by the background worker. Deployment backups may retain
          prior data according to the operator’s retention policy.
        </p>
        <h2>Beta limitations</h2>
        <p>
          Extraction, skill suggestions and compatibility scores can be wrong. Review every claim before
          exporting a CV. Scores are not hiring probabilities or automated rejection decisions. The beta
          focuses on English CVs; scanned documents require text extraction before upload.
        </p>
        <p>
          CV Studio uses conservative editing rules; it does not send your CV to an external text-generation
          service. Current tests and synthetic evaluation do not establish hiring validity or fairness.
        </p>
        <Link href="/feedback" className="text-link">
          Contact the beta team through feedback
        </Link>
        <Link href="/" className="text-link">
          Back to TalentLens
        </Link>
      </article>
    </main>
  );
}
