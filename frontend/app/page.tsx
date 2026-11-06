import Link from "next/link";
import {
  ArrowRight,
  FileText,
  ScanLine,
  ShieldCheck,
  Sparkles,
  BriefcaseBusiness,
  Fingerprint,
  Layers3,
  Check,
} from "lucide-react";
import { Brand } from "@/components/common";
import { Button } from "@/components/ui/button";
export default function Home() {
  return (
    <div className="landing">
      <nav className="landing-nav">
        <Brand />
        <div className="row">
          <Button asChild variant="ghost">
            <Link href="/login">Sign in</Link>
          </Button>
          <Button asChild>
            <Link href="/register">
              Get started <ArrowRight size={14} />
            </Link>
          </Button>
        </div>
      </nav>
      <main>
        <section className="landing-hero">
          <div>
            <span className="pill purple">
              <Sparkles size={12} /> A clearer view of your potential
            </span>
            <h1>
              Beyond keywords.
              <br />
              Closer to your
              <br />
              <em>next opportunity.</em>
            </h1>
            <p>
              Turn your resume into a clearer picture of your skills. Understand how your experience connects
              to a role—and what to demonstrate next.
            </p>
            <div className="row mt-7">
              <Button asChild>
                <Link href="/register">
                  Analyze my resume <ArrowRight size={15} />
                </Link>
              </Button>
              <Button asChild variant="outline">
                <Link href="/register?role=RECRUITER">
                  I’m hiring <BriefcaseBusiness size={15} />
                </Link>
              </Button>
            </div>
            <p className="!text-xs mt-6">
              <ShieldCheck size={14} className="inline mr-2" />
              Private documents. Transparent scoring. Human decisions.
            </p>
          </div>
          <div className="preview">
            <div className="row between">
              <span className="eyebrow">From document to direction</span>
              <span className="pill green">
                <Check size={12} /> You’re in control
              </span>
            </div>
            <div className="preview-flow">
              {[
                [FileText, "Your experience, structured", "PDF & DOCX → an editable qualification profile"],
                [ScanLine, "A match you can understand", "Semantic relevance + documented skill evidence"],
                [
                  Layers3,
                  "Your next step, made clear",
                  "Required skills, uncertainties, and a learning plan",
                ],
              ].map(([Icon, title, text], i) => {
                const Element = Icon as typeof FileText;
                return (
                  <div className="preview-item" key={i}>
                    <Element size={26} />
                    <div>
                      <strong>{String(title)}</strong>
                      <small>{String(text)}</small>
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="notice">
              <Fingerprint size={18} />
              Your resume is never added to a public candidate pool. Apply to a job to share it with that
              recruiter.
            </div>
          </div>
        </section>
        <section className="landing-features">
          <div className="grid-3">
            {[
              [
                "01",
                "Start with your story",
                "Upload your resume. Review extracted skills, experience, projects, and education. Correct anything that needs a second look.",
              ],
              [
                "02",
                "See the evidence",
                "Compare your qualifications with recruiter-confirmed requirements. Inspect the score components and the text behind each match.",
              ],
              [
                "03",
                "Move forward with clarity",
                "Get an evidence-based skill gap report. Apply with explicit consent, or keep your analysis completely private.",
              ],
            ].map(([n, title, text]) => (
              <article key={n} className="panel">
                <span className="eyebrow">{n} / THE WORKFLOW</span>
                <h2 className="mt-4">{title}</h2>
                <p className="muted text-sm mb-0">{text}</p>
              </article>
            ))}
          </div>
          <div className="notice mt-7">
            <ShieldCheck size={18} />
            TalentLens is a decision-support tool. Matching scores are engineering heuristics, not verified
            measures of ability or probabilities of getting hired. Recruiters remain responsible for reviewing
            applicants fairly.
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        TalentLens AI · Designed and built for a clearer view of qualifications · Mashiel Khan
      </footer>
    </div>
  );
}
