"use client";
import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, send } from "@/lib/api";
import { dateLabel, Empty, ErrorBox, Heading, Loading, Status, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { Application } from "@/types/api";
export default function Page() {
  const { data: user } = useUser(),
    cache = useQueryClient(),
    [search, setSearch] = useState("");
  const query = useQuery({ queryKey: ["applications"], queryFn: () => api<Application[]>("/applications") });
  const action = useMutation({
    mutationFn: ({ id, status }: { id: string; status?: string }) =>
      api(`/applications/${id}`, send(status ? "PATCH" : "DELETE", status ? { status } : undefined)),
    onSuccess: () => {
      cache.invalidateQueries({ queryKey: ["applications"] });
      cache.invalidateQueries({ queryKey: ["matches"] });
    },
  });
  const filtered = query.data?.filter((a) =>
    `${a.candidate_name} ${a.job_title} ${a.company}`.toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <Heading
        title="Applications"
        subtitle={
          user?.role === "RECRUITER"
            ? "Only applicants who explicitly shared their resume with your job appear here."
            : "Your shared resumes and the opportunities you’re exploring."
        }
      />
      <div className="stack">
        <ErrorBox error={action.error} />
        <label className="field">
          Search applications
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Candidate, job, or company"
          />
        </label>
        <section className="panel">
          {query.isPending ? (
            <Loading />
          ) : query.error ? (
            <ErrorBox error={query.error} />
          ) : !filtered?.length ? (
            <Empty title="No applications to show" href="/jobs" action="View jobs">
              {search
                ? "Try a different search."
                : "Applications appear after an applicant chooses a job and explicitly shares their resume."}
            </Empty>
          ) : (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{user?.role === "RECRUITER" ? "CANDIDATE" : "OPPORTUNITY"}</th>
                    <th>SHARED ON</th>
                    <th>STATUS</th>
                    <th>ACTIONS</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <Link
                          className="table-title"
                          href={user?.role === "RECRUITER" ? `/resumes/${a.resume_id}` : `/jobs/${a.job_id}`}
                        >
                          {user?.role === "RECRUITER" ? a.candidate_name : a.job_title}
                        </Link>
                        <span className="table-sub">
                          {user?.role === "RECRUITER" ? a.job_title : a.company}
                        </span>
                      </td>
                      <td className="muted">{dateLabel(a.consent_at)}</td>
                      <td>
                        <Status value={a.status} />
                      </td>
                      <td>
                        {user?.role === "RECRUITER" ? (
                          <select
                            className="!py-2"
                            aria-label={`Review status for ${a.candidate_name}`}
                            value={a.status}
                            disabled={action.isPending}
                            onChange={(e) => action.mutate({ id: a.id, status: e.target.value })}
                          >
                            {["SUBMITTED", "REVIEWED", "SHORTLISTED"].map((s) => (
                              <option key={s}>{s}</option>
                            ))}
                          </select>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            disabled={action.isPending}
                            onClick={() => {
                              if (
                                window.confirm(
                                  "Withdraw this application? The recruiter will lose access through this job.",
                                )
                              )
                                action.mutate({ id: a.id });
                            }}
                          >
                            Withdraw consent
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
        <div className="notice">
          Withdrawing an application removes recruiter access through that job and deletes the associated
          analyses. Previously downloaded documents cannot be recalled.
        </div>
      </div>
    </>
  );
}
