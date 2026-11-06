"use client";
import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Plus, MapPin, Clock, ArrowUpRight, BriefcaseBusiness, Search } from "lucide-react";
import { api } from "@/lib/api";
import { Empty, ErrorBox, Heading, Loading, Status, useUser } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { Job } from "@/types/api";
export default function Page() {
  const { data: user } = useUser(),
    recruiter = user?.role === "RECRUITER";
  const [search, setSearch] = useState(""),
    [term, setTerm] = useState("");
  const query = useQuery({
    queryKey: ["jobs", recruiter, term],
    queryFn: () => api<Job[]>(`/jobs?mine=${recruiter}&q=${encodeURIComponent(term)}`),
    enabled: !!user,
  });
  return (
    <>
      <Heading
        title={recruiter ? "Job management" : "Explore opportunities"}
        subtitle={
          recruiter
            ? "Clear requirements are the start of a meaningful match."
            : "Find a role. Compare your qualifications. Choose what comes next."
        }
      >
        {recruiter && (
          <Button asChild>
            <Link href="/jobs/new">
              <Plus size={15} />
              Create job
            </Link>
          </Button>
        )}
      </Heading>
      <form
        className="row mb-6"
        onSubmit={(e) => {
          e.preventDefault();
          setTerm(search);
        }}
      >
        <label className="flex-1">
          <span className="sr-only">Search jobs</span>
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search role, technology, or responsibility…"
          />
        </label>
        <Button variant="outline">
          <Search size={15} />
          Search
        </Button>
      </form>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorBox error={query.error} />
      ) : !query.data?.length ? (
        <section className="panel">
          <Empty
            title={
              term
                ? "No roles match that search"
                : recruiter
                  ? "Your next role starts here"
                  : "No published jobs yet"
            }
            href={recruiter ? "/jobs/new" : undefined}
            action="Create your first job"
          >
            {recruiter
              ? "Create a role and confirm its requirements to start receiving applications."
              : "Published roles will appear here when recruiters make them available."}
          </Empty>
        </section>
      ) : (
        <div className="grid-2">
          {query.data.map((job) => (
            <article className="panel job-card" key={job.id}>
              <div className="row between">
                <div className="row">
                  <span className="company-mark">
                    <BriefcaseBusiness size={20} />
                  </span>
                  <div>
                    <h2>{job.title}</h2>
                    <span className="muted text-xs">{job.company}</span>
                  </div>
                </div>
                {recruiter && <Status value={job.status} />}
              </div>
              <p className="job-description line-clamp-3">{job.description}</p>
              <div className="row job-meta">
                <span>
                  <MapPin size={12} />
                  {job.location}
                </span>
                <span>
                  <Clock size={12} />
                  {job.employment_type}
                </span>
                <span>{job.remote_policy}</span>
              </div>
              <div className="row mt-5">
                {job.required_skills.slice(0, 5).map((s) => (
                  <span className="skill" key={s.name}>
                    {s.name}
                  </span>
                ))}
              </div>
              <div className="row between mt-6 pt-4 border-t border-slate-100">
                <span className="text-xs muted">{job.required_skills.length} confirmed essential skills</span>
                <Button asChild variant="outline" size="sm">
                  <Link href={`/jobs/${job.id}`}>
                    {recruiter ? "Manage role" : "Explore role"}
                    <ArrowUpRight size={13} />
                  </Link>
                </Button>
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
