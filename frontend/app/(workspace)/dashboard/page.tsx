"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { motion } from "motion/react";
import {
  FileText,
  ScanLine,
  Sparkles,
  BriefcaseBusiness,
  ArrowRight,
  Plus,
  ShieldCheck,
  Users,
} from "lucide-react";
import { api } from "@/lib/api";
import { Empty, ErrorBox, Heading, Loading, ResponsibleNotice, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
import { Upload } from "@/components/resumes/upload";
import { ResumeTable } from "@/components/resumes/table";
import type { Analytics, Match, Resume } from "@/types/api";
export default function Dashboard() {
  const { data: user } = useUser();
  const { data, error, isPending } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => api<Analytics>("/analytics"),
    refetchInterval: 10000,
  });
  const { data: resumes = [] } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/resumes"),
    refetchInterval: 5000,
  });
  const { data: matches = [] } = useQuery({ queryKey: ["matches"], queryFn: () => api<Match[]>("/matches") });
  if (isPending) return <Loading />;
  if (error || !data) return <ErrorBox error={error} />;
  const recruiter = user?.role === "RECRUITER";
  const stats = recruiter
    ? [
        [BriefcaseBusiness, "Active jobs", data.active_jobs, "Published opportunities"],
        [Users, "Applications", data.applications, "Shared with explicit consent"],
        [ScanLine, "Completed analyses", data.analyses, "Evidence you can inspect"],
        [Sparkles, "Documented skills", data.documented_skills, "Across your applicant pool"],
      ]
    : [
        [FileText, "My resumes", data.resumes, "Your private documents"],
        [ScanLine, "Completed analyses", data.analyses, "Explained, never a black box"],
        [Sparkles, "Documented skills", data.documented_skills, "Extracted from your resumes"],
        [BriefcaseBusiness, "Applications", data.applications, "Opportunities in progress"],
      ];
  return (
    <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>
      <Heading title="Overview" subtitle="A little more clarity for your next big step.">
        <span className="pill">
          <ShieldCheck size={12} /> Private workspace
        </span>
      </Heading>
      <section className="welcome">
        <span className="eyebrow !text-[#9a8abe]">YOUR POTENTIAL, IN FOCUS</span>
        <h2>
          Welcome{user?.full_name ? `, ${user.full_name.split(" ")[0]}` : " back"}{" "}
          <span className="text-[#aa9bdd]">✦</span>
        </h2>
        <p>
          {recruiter
            ? "Connect the right qualifications with your next role. Build clear requirements and explore the evidence behind each application."
            : "Every experience tells a story. Let’s turn yours into clear insights and find the opportunities that fit."}
        </p>
        <div className="row">
          <Button asChild size="sm">
            <Link href={recruiter ? "/jobs/new" : "/resumes"}>
              <Plus size={14} />
              {recruiter ? "Create a job" : "Upload a resume"}
            </Link>
          </Button>
          <Button asChild size="sm" variant="ghost">
            <Link href={recruiter ? "/applications" : "/jobs"}>
              {recruiter ? "View applications" : "Explore opportunities"}
              <ArrowRight size={14} />
            </Link>
          </Button>
        </div>
        <div className="welcome-art" aria-hidden="true">
          <div className="orbit" />
          <div className="orbit" />
          <div className="document">
            <FileText size={55} />
          </div>
          <Sparkles size={22} className="absolute right-1 top-5" />
        </div>
      </section>
      <div className="stat-grid">
        {stats.map(([Icon, title, value, note]) => {
          const Element = Icon as typeof FileText;
          return (
            <article className="panel stat" key={String(title)}>
              <div className="row between">
                <span className="stat-title">{String(title)}</span>
                <span className="stat-icon">
                  <Element size={16} />
                </span>
              </div>
              <span className="stat-value">{String(value)}</span>
              <span className="stat-note">{String(note)}</span>
            </article>
          );
        })}
      </div>
      <div className="dashboard-grid">
        <div className="stack">
          {!recruiter && (
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Bring your experience into focus</h2>
                  <p>Upload a resume to get your personalized qualification profile.</p>
                </div>
                <span className="pill purple">PDF / DOCX</span>
              </div>
              <Upload />
            </section>
          )}
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>{recruiter ? "Recent candidate analyses" : "My resumes"}</h2>
                <p>
                  {recruiter
                    ? "Results based on your confirmed job criteria."
                    : "Your documents, organized and ready to explore."}
                </p>
              </div>
              <Link className="text-link" href={recruiter ? "/matches" : "/resumes"}>
                View all →
              </Link>
            </div>
            {recruiter ? (
              matches.slice(0, 4).map((m) => (
                <Link
                  className="row between py-3 border-b border-slate-100"
                  key={m.id}
                  href={`/matches/${m.id}`}
                >
                  <div>
                    <strong className="text-xs">{m.candidate_name}</strong>
                    <p className="muted text-xs mb-0">{m.job_title}</p>
                  </div>
                  <span className="pill purple">{m.compatibility_index.toFixed(1)} / 100</span>
                </Link>
              ))
            ) : (
              <ResumeTable resumes={resumes.slice(0, 4)} />
            )}
            {recruiter && !matches.length && (
              <Empty title="Ready when your applicants are">
                Create a job, receive consented applications, and run your first analysis.
              </Empty>
            )}
          </section>
        </div>
        <div className="stack">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>{recruiter ? "A thoughtful hiring workflow" : "Your path to a clearer match"}</h2>
                <p>A few steps. Insights you can act on.</p>
              </div>
              <Sparkles size={16} className="text-[#9b8bc7]" />
            </div>
            {(recruiter
              ? [
                  ["Define what matters", "Confirm required and preferred qualifications."],
                  ["Review real applications", "Only applicants who choose to share appear here."],
                  ["Explore the evidence", "Compare qualifications and make your own decision."],
                ]
              : [
                  ["Upload & review", "See your experience as structured, editable information."],
                  ["Find your next role", "Compare your resume with published opportunities."],
                  ["Close the evidence gaps", "Discover what to demonstrate or develop next."],
                ]
            ).map(([title, text], i) => (
              <div className="step" key={title}>
                <span className="step-index">0{i + 1}</span>
                <div>
                  <strong>{title}</strong>
                  <p>{text}</p>
                </div>
              </div>
            ))}
          </section>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <h2>Your documented skills</h2>
                <p>Every skill starts with evidence.</p>
              </div>
            </div>
            {data.skills.length ? (
              <div className="row">
                {data.skills.slice(0, 10).map((s) => (
                  <span className="skill" key={s.name}>
                    {s.name}
                  </span>
                ))}
              </div>
            ) : (
              <p className="text-xs muted mb-0">
                Skills will appear here after resumes have been processed. No assumptions, just what’s
                documented.
              </p>
            )}
            <div className="notice mt-5">
              <ShieldCheck size={15} />
              <span>Technology mentions show evidence, not verified proficiency.</span>
            </div>
          </section>
        </div>
      </div>
      <div className="mt-6">
        <ResponsibleNotice />
      </div>
    </motion.div>
  );
}
