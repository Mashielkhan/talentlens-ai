"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Sparkles, Save } from "lucide-react";
import { api, send } from "@/lib/api";
import { ErrorBox } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { Job, JobInput, Requirement, Skill } from "@/types/api";

export function parseRequirements(value: string): Requirement[] {
  return value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
    .map((s) => {
      const [name, weight] = s.split(":");
      return { name: name.trim(), weight: weight ? Number(weight) : 1 };
    });
}
export function JobForm({ job, company = "" }: { job?: Job; company?: string }) {
  const router = useRouter(),
    cache = useQueryClient();
  const [description, setDescription] = useState(job?.description || "");
  const [suggestions, setSuggestions] = useState<Skill[]>([]);
  const suggest = useMutation({
    mutationFn: () =>
      api<{ suggested_skills: Skill[] }>("/jobs/suggest", send("POST", { text: description })),
    onSuccess: (data) => setSuggestions(data.suggested_skills),
  });
  const save = useMutation({
    mutationFn: (value: JobInput) =>
      api<Job>(job ? `/jobs/${job.id}` : "/jobs", send(job ? "PATCH" : "POST", value)),
    onSuccess: (created) => {
      cache.invalidateQueries({ queryKey: ["jobs"] });
      cache.invalidateQueries({ queryKey: ["job", created.id] });
      cache.invalidateQueries({ queryKey: ["matches"] });
      router.push(`/jobs/${created.id}`);
    },
  });
  function submit(form: FormData) {
    const string = (key: string) => String(form.get(key) || "");
    save.mutate({
      title: string("title"),
      company: string("company"),
      description,
      location: string("location"),
      employment_type: string("employment_type"),
      remote_policy: string("remote_policy"),
      status: string("status"),
      required_skills: parseRequirements(string("required")),
      preferred_skills: parseRequirements(string("preferred")),
      min_experience_months: Number(form.get("months")),
      education_requirement: string("education"),
      requirements_confirmed: form.get("confirmed") === "on",
    });
  }
  return (
    <form action={submit} className="panel stack">
      <ErrorBox error={save.error || suggest.error} />
      <div className="form-grid">
        <label className="field">
          Job title
          <input
            name="title"
            required
            minLength={3}
            maxLength={160}
            defaultValue={job?.title}
            placeholder="e.g. Python Backend Engineer"
          />
        </label>
        <label className="field">
          Company
          <input
            name="company"
            required
            minLength={2}
            maxLength={160}
            defaultValue={job?.company || company}
          />
        </label>
        <label className="field full">
          Responsibilities & qualifications
          <textarea
            name="description"
            required
            minLength={40}
            maxLength={30000}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="!min-h-48"
            placeholder="Describe the work and the qualifications relevant to this role. Exclude demographic criteria."
          />
        </label>
        <div className="full">
          <Button
            type="button"
            variant="outline"
            disabled={description.length < 20 || suggest.isPending}
            onClick={() => suggest.mutate()}
          >
            <Sparkles size={14} />
            Suggest skills from description
          </Button>
          {suggestions.length > 0 && (
            <div className="notice mt-3">
              <div>
                <strong>Review these suggestions</strong>
                <p className="mb-2 text-xs">
                  Place relevant skills into required or preferred below. No suggestion is mandatory
                  automatically.
                </p>
                <div className="row">
                  {suggestions.map((s) => (
                    <span className="skill" key={s.name}>
                      {s.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
        <label className="field full">
          Required skills · comma-separated, optional weights 1–5
          <input
            name="required"
            defaultValue={job?.required_skills.map((s) => `${s.name}:${s.weight}`).join(", ")}
            placeholder="Python:5, FastAPI:4, PostgreSQL:3"
          />
        </label>
        <label className="field full">
          Preferred skills
          <input
            name="preferred"
            defaultValue={job?.preferred_skills.map((s) => `${s.name}:${s.weight}`).join(", ")}
            placeholder="Docker, AWS"
          />
        </label>
        <label className="field">
          Minimum relevant experience (months)
          <input
            name="months"
            type="number"
            min={0}
            max={600}
            defaultValue={job?.min_experience_months || 0}
          />
        </label>
        <label className="field">
          Education requirement (optional)
          <input
            name="education"
            maxLength={255}
            defaultValue={job?.education_requirement}
            placeholder="e.g. Computer Science"
          />
        </label>
        <label className="field">
          Location
          <input name="location" maxLength={160} defaultValue={job?.location || "Remote"} />
        </label>
        <label className="field">
          Work arrangement
          <select name="remote_policy" defaultValue={job?.remote_policy || "Remote"}>
            {["Remote", "Hybrid", "On-site"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Employment type
          <select name="employment_type" defaultValue={job?.employment_type || "Full-time"}>
            {["Full-time", "Part-time", "Contract", "Internship"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label className="field">
          Visibility
          <select name="status" defaultValue={job?.status || "DRAFT"}>
            {["DRAFT", "PUBLISHED", "ARCHIVED"].map((v) => (
              <option key={v}>{v}</option>
            ))}
          </select>
        </label>
        <label className="row full text-xs muted">
          <input name="confirmed" type="checkbox" defaultChecked={job?.requirements_confirmed} />I reviewed
          these requirements and confirm they are relevant to this job. Required before publishing or
          matching.
        </label>
      </div>
      <div className="row">
        <Button disabled={save.isPending}>
          <Save size={15} />
          {save.isPending ? "Saving…" : "Save job"}
        </Button>
        <span className="muted text-xs">Changing a job invalidates its previous analyses.</span>
      </div>
    </form>
  );
}
