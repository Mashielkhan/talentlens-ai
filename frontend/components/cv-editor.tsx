"use client";
import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { CvContent, CvDraft } from "@/types/api";

const fields: { key: keyof CvContent; label: string; max: number; rows: number }[] = [
  { key: "name", label: "Full name", max: 120, rows: 1 },
  { key: "email", label: "Email", max: 254, rows: 1 },
  { key: "phone", label: "Phone", max: 100, rows: 1 },
  { key: "links", label: "Professional links", max: 1000, rows: 2 },
  { key: "summary", label: "Summary", max: 4000, rows: 4 },
  { key: "skills", label: "Skills", max: 4000, rows: 3 },
  { key: "experience", label: "Experience", max: 15000, rows: 8 },
  { key: "education", label: "Education", max: 6000, rows: 4 },
  { key: "projects", label: "Projects", max: 10000, rows: 6 },
  { key: "certifications", label: "Certifications", max: 4000, rows: 3 },
];

export function CvEditor({ draft }: { draft: CvDraft }) {
  const [content, setContent] = useState(draft.content),
    [confirmed, setConfirmed] = useState(false);
  const cache = useQueryClient(),
    router = useRouter();
  const dirty = JSON.stringify(content) !== JSON.stringify(draft.content);
  const approved = draft.approved_revision === draft.revision && !dirty && !draft.source_outdated;
  const action = useMutation({
    mutationFn: ({ method, suffix = "", body }: { method: string; suffix?: string; body?: unknown }) =>
      api<CvDraft>(`/studio/${draft.id}${suffix}`, send(method, body)),
    onSuccess: (updated, variables) => {
      cache.invalidateQueries({ queryKey: ["cv-drafts"] });
      if (variables.method === "DELETE") router.push("/studio");
      else {
        cache.setQueryData(["cv-draft", draft.id], updated);
        setConfirmed(false);
      }
    },
  });
  function edit(key: keyof CvContent, value: string) {
    setContent((previous) => ({ ...previous, [key]: value }));
    setConfirmed(false);
  }
  return (
    <>
      <Link href="/studio" className="text-link">
        ← All CV drafts
      </Link>
      <Heading
        title={draft.title}
        subtitle={`Revision ${draft.revision} · ${approved ? "Approved for export" : "Review your facts before exporting"}`}
      />
      <ErrorBox error={action.error} />
      {draft.source_outdated && (
        <div role="alert" className="error mb-5">
          The original resume changed. This draft is read-only. <Link href="/studio">Create a new draft</Link>{" "}
          from its processed version.
        </div>
      )}
      <div className="grid-2">
        <section className="panel">
          <h2>Your CV</h2>
          <p className="muted text-xs">
            Edit only claims you can support. Empty sections are omitted from exports. PDF uses a simple
            single-column layout; review non-Latin text in the DOCX export.
          </p>
          <fieldset className="stack min-w-0" disabled={action.isPending || draft.source_outdated}>
            {fields.map((field) => (
              <div key={field.key} className="field">
                <label htmlFor={`cv-${field.key}`}>{field.label}</label>
                {field.rows === 1 ? (
                  <input
                    id={`cv-${field.key}`}
                    value={content[field.key]}
                    maxLength={field.max}
                    onChange={(e) => edit(field.key, e.target.value)}
                  />
                ) : (
                  <textarea
                    id={`cv-${field.key}`}
                    value={content[field.key]}
                    maxLength={field.max}
                    rows={field.rows}
                    onChange={(e) => edit(field.key, e.target.value)}
                  />
                )}
              </div>
            ))}
            <Button
              disabled={!dirty}
              onClick={() => action.mutate({ method: "PATCH", body: { revision: draft.revision, content } })}
            >
              Save draft
            </Button>
            {dirty && (
              <p role="status" className="muted text-xs">
                You have unsaved edits. Save before approving or exporting.
              </p>
            )}
          </fieldset>
        </section>
        <div className="stack">
          <section className="panel">
            <h2>Suggested wording</h2>
            <p className="muted text-xs">
              These suggestions shorten your existing wording. They do not add achievements or qualifications.
            </p>
            {!draft.guidance.suggestions.length && (
              <p className="muted">
                No supported wording replacements were found. Use the review prompts below to add your own
                details.
              </p>
            )}
            {draft.guidance.suggestions.map((s) => {
              const available = content[s.section].includes(s.original);
              return (
                <div className="evidence" key={s.id}>
                  <small>Original · {s.section}</small>
                  <p className="section-text">{s.original}</p>
                  <strong>Suggested</strong>
                  <p className="section-text">{s.replacement}</p>
                  <p className="muted text-xs">{s.reason}</p>
                  <Button
                    variant="outline"
                    disabled={!available || action.isPending || draft.source_outdated}
                    onClick={() => edit(s.section, content[s.section].replace(s.original, s.replacement))}
                  >
                    {available ? "Use this wording" : "Applied or source edited"}
                  </Button>
                </div>
              );
            })}
          </section>
          <section className="panel">
            <h2>Job-specific review</h2>
            <h3>Documented relevant skills</h3>
            <p>
              {draft.guidance.documented_target_skills.join(", ") ||
                "None recognized in the current skill catalog."}
            </p>
            <h3>Not documented in the source</h3>
            <p>
              {draft.guidance.not_documented_target_skills.join(", ") ||
                "No additional catalogued skills identified."}
            </p>
            <p className="muted text-xs">
              Mention these only if you actually have the experience, with a concrete example. A missing
              mention does not prove a missing skill.
            </p>
            {draft.guidance.prompts.map((prompt) => (
              <p key={prompt} className="notice">
                {prompt}
              </p>
            ))}
            <details>
              <summary>View target job description</summary>
              <p className="section-text">{draft.target_description}</p>
            </details>
            <details className="mt-5">
              <summary>View original extracted content</summary>
              {fields
                .filter((f) => draft.original[f.key])
                .map((f) => (
                  <div key={f.key}>
                    <h3>{f.label}</h3>
                    <p className="section-text">{draft.original[f.key]}</p>
                  </div>
                ))}
            </details>
          </section>
          <section className="panel stack">
            <h2>Review and export</h2>
            <label className="row text-sm">
              <input
                type="checkbox"
                checked={confirmed}
                disabled={dirty || action.isPending || draft.source_outdated}
                onChange={(e) => setConfirmed(e.target.checked)}
              />
              I reviewed this saved revision and confirm that its facts are accurate.
            </label>
            <Button
              disabled={!confirmed || dirty || action.isPending || draft.source_outdated}
              onClick={() =>
                action.mutate({
                  method: "POST",
                  suffix: "/approve",
                  body: { revision: draft.revision, facts_confirmed: true },
                })
              }
            >
              Approve this revision
            </Button>
            {approved && (
              <div className="row">
                <Button asChild>
                  <a href={`/api/v1/studio/${draft.id}/export/pdf`}>Download CV PDF</a>
                </Button>
                <Button variant="outline" asChild>
                  <a href={`/api/v1/studio/${draft.id}/export/docx`}>Download CV DOCX</a>
                </Button>
              </div>
            )}
            <p className="muted text-xs">
              Editing the draft removes approval. This CV is not automatically shared with recruiters.
            </p>
            <Button
              variant="destructive"
              disabled={action.isPending}
              onClick={() => {
                if (window.confirm("Delete this private CV draft? Your uploaded resume will remain."))
                  action.mutate({ method: "DELETE" });
              }}
            >
              Delete draft
            </Button>
          </section>
        </div>
      </div>
    </>
  );
}
