"use client";
import { use, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, ScanLine, Trash2, ArrowLeft, Send } from "lucide-react";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading, Loading, ResponsibleNotice, Status, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
import { JobForm } from "@/components/jobs/job-form";
import { TaskProgress } from "@/components/matching/task-progress";
import type { Job, Resume, Task } from "@/types/api";
export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params),
    { data: user } = useUser(),
    cache = useQueryClient(),
    router = useRouter();
  const [editing, setEditing] = useState(false),
    [resumeId, setResumeId] = useState(""),
    [consent, setConsent] = useState(false),
    [task, setTask] = useState<string>(),
    [applied, setApplied] = useState(false);
  const query = useQuery({ queryKey: ["job", id], queryFn: () => api<Job>(`/jobs/${id}`) });
  const { data: resumes = [] } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/resumes"),
    enabled: user?.role === "APPLICANT",
  });
  const mutate = useMutation({
    mutationFn: ({
      endpoint,
      method = "POST",
      body,
    }: {
      endpoint: string;
      method?: string;
      body?: unknown;
    }) => api<Task | undefined>(endpoint, send(method, body)),
    onSuccess: (value, variables) => {
      if (variables.method === "DELETE") {
        cache.invalidateQueries({ queryKey: ["jobs"] });
        router.push("/jobs");
      } else if (variables.endpoint.endsWith("/applications")) {
        setApplied(true);
        cache.invalidateQueries({ queryKey: ["applications"] });
      } else if (value?.id) setTask(value.id);
    },
  });
  if (query.isPending) return <Loading />;
  if (!query.data) return <ErrorBox error={query.error} />;
  const job = query.data,
    owner = job.recruiter_id === user?.id;
  return (
    <>
      <Link href="/jobs" className="text-link">
        <ArrowLeft size={12} className="inline" /> Opportunities
      </Link>
      <Heading title={job.title} subtitle={`${job.company} · ${job.location} · ${job.remote_policy}`}>
        <Status value={job.status} />
      </Heading>
      <div className="stack">
        <ErrorBox error={mutate.error} />
        {owner && (
          <div className="row">
            <Button variant="outline" onClick={() => setEditing(!editing)}>
              <Pencil size={14} />
              {editing ? "Close editor" : "Edit requirements"}
            </Button>
            <Button
              disabled={mutate.isPending || !job.requirements_confirmed}
              onClick={() => mutate.mutate({ endpoint: `/jobs/${id}/match` })}
            >
              <ScanLine size={14} />
              Analyze applicants
            </Button>
            <Button
              variant="destructive"
              disabled={mutate.isPending}
              onClick={() => {
                if (window.confirm("Delete this job and its applications and analyses?"))
                  mutate.mutate({ endpoint: `/jobs/${id}`, method: "DELETE" });
              }}
            >
              <Trash2 size={14} />
              Delete job
            </Button>
          </div>
        )}
        {editing ? (
          <JobForm job={job} />
        ) : (
          <>
            <section className="panel">
              <h2>About this opportunity</h2>
              <p className="section-text">{job.description}</p>
              <div className="row mt-5">
                <span className="pill">{job.employment_type}</span>
                <span className="pill">
                  {job.min_experience_months
                    ? `${job.min_experience_months} months relevant experience`
                    : "No minimum experience specified"}
                </span>
              </div>
            </section>
            <div className="grid-2">
              <section className="panel">
                <h2>Required skills</h2>
                <div className="row">
                  {job.required_skills.map((s) => (
                    <span className="skill" key={s.name}>
                      {s.name} · weight {s.weight}
                    </span>
                  ))}
                </div>
                <p className="muted text-xs mt-4 mb-0">
                  {job.required_skills.length
                    ? "Coverage is weighted by the importance shown."
                    : "No mandatory skills have been specified."}
                </p>
              </section>
              <section className="panel">
                <h2>Preferred skills</h2>
                <div className="row">
                  {job.preferred_skills.map((s) => (
                    <span className="skill" key={s.name}>
                      {s.name}
                    </span>
                  ))}
                </div>
                <p className="muted text-xs mt-4">
                  Education: {job.education_requirement || "No requirement specified"}
                </p>
              </section>
            </div>
          </>
        )}
        {user?.role === "APPLICANT" && (
          <section className="panel stack">
            <h2>See how your experience connects</h2>
            <label className="field">
              Choose a processed resume
              <select value={resumeId} onChange={(e) => setResumeId(e.target.value)}>
                <option value="">Select a resume</option>
                {resumes
                  .filter((r) => r.status === "COMPLETED")
                  .map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.original_filename}
                    </option>
                  ))}
              </select>
            </label>
            {!resumes.some((r) => r.status === "COMPLETED") && (
              <Link className="text-link" href="/resumes">
                Upload and process a resume first →
              </Link>
            )}
            <div>
              <Button
                variant="outline"
                disabled={!resumeId || mutate.isPending}
                onClick={() =>
                  mutate.mutate({ endpoint: "/skill-gap/analyze", body: { resume_id: resumeId, job_id: id } })
                }
              >
                <ScanLine size={14} />
                Analyze privately
              </Button>
              <p className="text-xs muted mt-2 mb-0">
                Private analysis does not share your resume with the recruiter.
              </p>
            </div>
            <label className="row text-xs muted">
              <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />I
              consent to share this resume and its qualification profile with {job.company} for this job. I
              can withdraw the application later.
            </label>
            <div>
              <Button
                disabled={!resumeId || !consent || mutate.isPending || applied}
                onClick={() =>
                  mutate.mutate({
                    endpoint: `/jobs/${id}/applications`,
                    body: { resume_id: resumeId, consent: true },
                  })
                }
              >
                <Send size={14} />
                {applied ? "Application submitted" : "Submit application"}
              </Button>
            </div>
          </section>
        )}
        {task && <TaskProgress id={task} />}
        <ResponsibleNotice />
      </div>
    </>
  );
}
