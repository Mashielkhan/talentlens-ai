"use client";
import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Download, ArrowUpRight } from "lucide-react";
import { api } from "@/lib/api";
import { Empty, ErrorBox, Heading, Loading, ResponsibleNotice, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
import { DistributionChart } from "@/components/analytics/charts";
import type { Analytics, Match } from "@/types/api";
export default function Page() {
  const { data: user } = useUser(),
    [job, setJob] = useState(""),
    [selected, setSelected] = useState<string[]>([]);
  const query = useQuery({
    queryKey: ["matches"],
    queryFn: () => api<Match[]>("/matches"),
    refetchInterval: 6000,
  });
  const { data: analytics } = useQuery({
    queryKey: ["analytics"],
    queryFn: () => api<Analytics>("/analytics"),
  });
  const all = query.data || [],
    filtered = all.filter((m) => !job || m.job_id === job),
    jobs = [...new Map(all.map((m) => [m.job_id, m.job_title])).entries()];
  const chosen = filtered.filter((m) => selected.includes(m.id)),
    comparable = chosen.length >= 2 && chosen.length <= 4 && new Set(chosen.map((m) => m.job_id)).size === 1;
  function select(id: string) {
    setSelected((current) =>
      current.includes(id)
        ? current.filter((s) => s !== id)
        : current.length < 4
          ? [...current, id]
          : current,
    );
  }
  return (
    <>
      <Heading
        title={user?.role === "RECRUITER" ? "Candidate matching" : "My analyses"}
        subtitle="Transparent relevance. Documented evidence. Clear next steps."
      />
      <div className="stack">
        <ResponsibleNotice />
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorBox error={query.error} />
        ) : !all.length ? (
          <section className="panel">
            <Empty title="Your first analysis is one step away" href="/jobs" action="Explore jobs">
              Choose a job and run a qualification analysis. Your real results will appear here.
            </Empty>
          </section>
        ) : (
          <>
            <div className="row between">
              <label className="field min-w-64">
                Filter by role
                <select
                  value={job}
                  onChange={(e) => {
                    setJob(e.target.value);
                    setSelected([]);
                  }}
                >
                  <option value="">All roles</option>
                  {jobs.map(([id, title]) => (
                    <option key={id} value={id}>
                      {title}
                    </option>
                  ))}
                </select>
              </label>
              {comparable && (
                <Button asChild variant="outline">
                  <a href={`/api/v1/reports/compare?${chosen.map((m) => `ids=${m.id}`).join("&")}`}>
                    <Download size={14} />
                    Export comparison
                  </a>
                </Button>
              )}
            </div>
            <section className="panel table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>COMPARE</th>
                    <th>{user?.role === "RECRUITER" ? "CANDIDATE" : "RESUME"}</th>
                    <th>ROLE</th>
                    <th>COMPATIBILITY INDEX</th>
                    <th>REQUIRED SKILLS</th>
                    <th>DETAILS</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((m) => (
                    <tr key={m.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selected.includes(m.id)}
                          onChange={() => select(m.id)}
                          aria-label={`Compare ${m.candidate_name} ${m.job_title}`}
                        />
                      </td>
                      <td>
                        <strong className="table-title">
                          {user?.role === "RECRUITER" ? m.candidate_name : m.resume_filename}
                        </strong>
                      </td>
                      <td className="muted">{m.job_title}</td>
                      <td>
                        <span className="pill purple">{m.compatibility_index.toFixed(1)} / 100</span>
                      </td>
                      <td className="muted">
                        {m.matched_skills.length} documented · {m.not_documented_required_skills.length} not
                        found
                      </td>
                      <td>
                        <Link href={`/matches/${m.id}`} className="text-link">
                          Inspect <ArrowUpRight size={12} className="inline" />
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="muted text-xs mt-4 mb-0">
                Compare two to four analyses for the same role. Rankings are relevance estimates, never
                automatic hiring decisions.
              </p>
            </section>
            {comparable && (
              <section className="panel table-wrap">
                <h2>Side-by-side evidence</h2>
                <table>
                  <thead>
                    <tr>
                      <th>CRITERION</th>
                      {chosen.map((m) => (
                        <th key={m.id}>{m.candidate_name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {["semantic_relevance", "required_skills", "experience", "education"].map((key) => (
                      <tr key={key}>
                        <td className="capitalize">{key.replaceAll("_", " ")}</td>
                        {chosen.map((m) => (
                          <td key={m.id}>{m.score_breakdown[key]?.toFixed(1) ?? "Unknown / N/A"}</td>
                        ))}
                      </tr>
                    ))}
                    <tr>
                      <td>Required skills not documented</td>
                      {chosen.map((m) => (
                        <td key={m.id}>{m.not_documented_required_skills.join(", ") || "None"}</td>
                      ))}
                    </tr>
                    <tr>
                      <td>Relevant experience</td>
                      {chosen.map((m) => (
                        <td key={m.id}>
                          {m.relevant_experience_months === null
                            ? "Not established"
                            : `${m.relevant_experience_months} months`}
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </section>
            )}
            {analytics && (
              <div className="grid-2">
                <section className="panel">
                  <h2>Analysis distribution</h2>
                  <p className="muted text-xs">Current results only. Count by relevance index range.</p>
                  <DistributionChart data={analytics.score_distribution} />
                </section>
                <section className="panel">
                  <h2>Frequently undocumented requirements</h2>
                  {analytics.gaps.length ? (
                    analytics.gaps.map((g) => (
                      <div key={g.name} className="row between py-2">
                        <span className="muted text-xs">{g.name}</span>
                        <span className="pill">
                          {g.count} {g.count === 1 ? "analysis" : "analyses"}
                        </span>
                      </div>
                    ))
                  ) : (
                    <p className="muted text-xs">No undocumented required skills in current results.</p>
                  )}
                </section>
              </div>
            )}
          </>
        )}
      </div>
    </>
  );
}
