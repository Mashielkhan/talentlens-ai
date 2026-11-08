"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading, Loading } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { CvDraft, Resume } from "@/types/api";

export default function StudioPage() {
  const router = useRouter();
  const resumes = useQuery({ queryKey: ["resumes"], queryFn: () => api<Resume[]>("/resumes") });
  const drafts = useQuery({ queryKey: ["cv-drafts"], queryFn: () => api<CvDraft[]>("/studio") });
  const create = useMutation({
    mutationFn: (body: unknown) => api<CvDraft>("/studio", send("POST", body)),
    onSuccess: (draft) => router.push(`/studio/${draft.id}`),
  });
  return (
    <>
      <Heading
        title="CV Studio"
        subtitle="Turn your documented experience into a CV you can review, tailor and export."
      />
      <div className="notice mb-5">
        Private beta · Your original file stays unchanged. Drafts are visible only to you, including when you
        apply to a job.
      </div>
      <div className="grid-2">
        <section className="panel">
          <h2>Create a tailored draft</h2>
          <ErrorBox error={resumes.error || create.error} />
          {resumes.isPending ? (
            <Loading />
          ) : (
            <form
              className="stack"
              onSubmit={(event) => {
                event.preventDefault();
                const values = new FormData(event.currentTarget);
                create.mutate(Object.fromEntries(values));
              }}
            >
              <label className="field">
                Processed resume
                <select name="resume_id" required defaultValue="">
                  <option value="" disabled>
                    Choose a resume
                  </option>
                  {resumes.data
                    ?.filter((r) => r.status === "COMPLETED")
                    .map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.original_filename}
                      </option>
                    ))}
                </select>
              </label>
              <Link className="text-link" href="/resumes">
                Upload or review a resume
              </Link>
              <label className="field">
                Draft title
                <input
                  name="title"
                  required
                  minLength={3}
                  maxLength={160}
                  placeholder="Backend developer application"
                />
              </label>
              <label className="field">
                Target job description
                <textarea
                  name="target_description"
                  required
                  minLength={40}
                  maxLength={20000}
                  rows={8}
                  placeholder="Paste the responsibilities and qualifications here…"
                />
              </label>
              <p className="muted text-xs">
                This job description stays in your private draft. It does not create a public job listing.
              </p>
              <Button disabled={create.isPending} type="submit">
                {create.isPending ? "Preparing draft…" : "Create CV draft"}
              </Button>
            </form>
          )}
        </section>
        <section className="panel">
          <h2>Your drafts</h2>
          <ErrorBox error={drafts.error} />
          {drafts.isPending ? (
            <Loading />
          ) : !drafts.data?.length ? (
            <p className="muted">Your saved drafts will appear here. Start with a processed resume.</p>
          ) : (
            <div className="stack">
              {drafts.data.map((d) => (
                <Link className="evidence" href={`/studio/${d.id}`} key={d.id}>
                  <strong>{d.title}</strong>
                  <p className="muted text-xs">
                    Revision {d.revision} ·{" "}
                    {d.source_outdated
                      ? "Source changed"
                      : d.approved_revision === d.revision
                        ? "Approved for export"
                        : "Needs review"}
                  </p>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </>
  );
}
