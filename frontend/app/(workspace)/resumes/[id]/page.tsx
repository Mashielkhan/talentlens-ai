"use client";
import { use, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, RefreshCw, Trash2, Pencil, Check, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { api, send } from "@/lib/api";
import { ErrorBox, Heading, Loading, ResponsibleNotice, Status, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { Resume } from "@/types/api";

export default function ResumePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params),
    cache = useQueryClient(),
    router = useRouter(),
    { data: user } = useUser();
  const [editing, setEditing] = useState(false);
  const query = useQuery({
    queryKey: ["resume", id],
    queryFn: () => api<Resume>(`/resumes/${id}`),
    refetchInterval: (q) =>
      ["PENDING", "PROCESSING", "RETRYING"].includes(q.state.data?.status || "") ? 3000 : false,
  });
  const action = useMutation({
    mutationFn: ({ method, suffix = "", body }: { method: string; suffix?: string; body?: unknown }) =>
      api(`/resumes/${id}${suffix}`, send(method, body)),
    onSuccess: (_, variables) => {
      cache.invalidateQueries({ queryKey: ["resume", id] });
      cache.invalidateQueries({ queryKey: ["resumes"] });
      cache.invalidateQueries({ queryKey: ["matches"] });
      setEditing(false);
      if (variables.method === "DELETE") router.push("/resumes");
    },
  });
  if (query.isPending) return <Loading />;
  if (!query.data) return <ErrorBox error={query.error} />;
  const r = query.data,
    p = r.parsed_data,
    owner = user?.role === "APPLICANT";
  function save(form: FormData) {
    const sections: Record<string, string> = {};
    for (const key of ["summary", "experience", "education", "projects", "certifications"])
      sections[key] = String(form.get(key) || "");
    action.mutate({
      method: "PATCH",
      body: {
        contact: {
          name: String(form.get("name") || ""),
          email: String(form.get("email") || ""),
          phone: String(form.get("phone") || ""),
        },
        skills: String(form.get("skills") || "")
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean),
        sections,
      },
    });
  }
  return (
    <>
      <Link href="/resumes" className="text-link">
        <ArrowLeft size={12} className="inline" /> My resumes
      </Link>
      <Heading title={r.original_filename} subtitle={`Version ${r.version} · ${r.stage}`}>
        <Status value={r.status} />
      </Heading>
      <div className="stack">
        <ErrorBox error={action.error} />
        <div className="row">
          <Button variant="outline" asChild>
            <a href={`/api/v1/resumes/${id}/download`}>
              <Download size={14} />
              Download original
            </a>
          </Button>
          {owner && (
            <>
              <Button
                variant="outline"
                disabled={action.isPending || ["PENDING", "PROCESSING", "RETRYING"].includes(r.status)}
                onClick={() => action.mutate({ method: "POST", suffix: "/reprocess" })}
              >
                <RefreshCw size={14} />
                Reprocess
              </Button>
              {r.status === "COMPLETED" && (
                <Button variant="outline" onClick={() => setEditing(!editing)}>
                  <Pencil size={14} />
                  {editing ? "Cancel editing" : "Correct extraction"}
                </Button>
              )}
              <Button
                variant="destructive"
                disabled={action.isPending}
                onClick={() => {
                  if (
                    window.confirm(
                      "Delete this resume, its applications, and all matching results? This cannot be undone.",
                    )
                  )
                    action.mutate({ method: "DELETE" });
                }}
              >
                <Trash2 size={14} />
                Delete
              </Button>
            </>
          )}
        </div>
        {r.error_code && (
          <div className="error" role="alert">
            Processing could not finish: {r.error_code}.{" "}
            {r.error_code.includes("OCR")
              ? "Upload a text-based PDF or DOCX. OCR is not enabled."
              : "Check the document or worker service, then reprocess."}
          </div>
        )}
        {["PENDING", "PROCESSING", "RETRYING"].includes(r.status) && (
          <section className="panel">
            <h2>Bringing your qualifications into focus</h2>
            <p className="muted">
              {r.stage}. This page updates automatically. Processing requires the Celery worker and downloaded
              NLP models.
            </p>
            <div className="skeleton !h-5" />
          </section>
        )}
        {editing ? (
          <form action={save} className="panel stack">
            <h2>Review and correct your profile</h2>
            <p className="muted text-xs">
              Corrections are labeled applicant-confirmed. Saving reprocesses your profile and invalidates
              previous matches.
            </p>
            <div className="form-grid">
              {["name", "email", "phone"].map((field) => (
                <label className="field" key={field}>
                  {field}
                  <input name={field} defaultValue={String(p.contact?.[field] || "")} maxLength={300} />
                </label>
              ))}
              <label className="field full">
                Documented skills (comma-separated)
                <input name="skills" defaultValue={p.skills?.map((s) => s.name).join(", ")} />
              </label>
              {["summary", "experience", "education", "projects", "certifications"].map((section) => (
                <label key={section} className="field full">
                  {section}
                  <textarea name={section} defaultValue={p.sections?.[section] || ""} maxLength={20000} />
                </label>
              ))}
            </div>
            <Button disabled={action.isPending} type="submit">
              <Check size={15} />
              Save and reprocess
            </Button>
          </form>
        ) : (
          r.status === "COMPLETED" && (
            <>
              <div className="grid-2">
                <section className="panel">
                  <h2>Contact details</h2>
                  {Object.entries(p.contact || {}).map(([key, value]) => (
                    <div className="row between py-2" key={key}>
                      <span className="muted text-xs capitalize">{key}</span>
                      <span className="text-xs break-all">
                        {Array.isArray(value)
                          ? value.join(", ") || "Not documented"
                          : value || "Not documented"}
                      </span>
                    </div>
                  ))}
                </section>
                <section className="panel">
                  <h2>Documented skills</h2>
                  <div className="row">
                    {p.skills?.map((s) => (
                      <span title={`${s.source_section}: ${s.evidence}`} className="skill" key={s.name}>
                        {s.name}
                        {s.user_verified && " ✓"}
                      </span>
                    ))}
                  </div>
                  <p className="muted text-xs mt-5 mb-0">
                    Technology mentions are evidence, not proof of proficiency.
                  </p>
                </section>
              </div>
              {["summary", "experience", "education", "projects", "certifications"]
                .filter((k) => p.sections?.[k])
                .map((key) => (
                  <section key={key} className="panel">
                    <h2 className="capitalize">{key}</h2>
                    <p className="section-text">{p.sections?.[key]}</p>
                  </section>
                ))}
              <section className="panel">
                <h2>Extraction evidence</h2>
                {p.skills?.map((s) => (
                  <div className="evidence" key={s.name}>
                    <strong>
                      {s.name} · {s.source_section}
                    </strong>
                    <p>{s.evidence}</p>
                  </div>
                ))}
                <h3 className="mt-6">Review notes</h3>
                {p.uncertainties?.map((note) => (
                  <p key={note} className="muted text-xs">
                    {note}
                  </p>
                ))}
              </section>
            </>
          )
        )}
        <ResponsibleNotice />
      </div>
    </>
  );
}
