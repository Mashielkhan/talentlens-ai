"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Heading, ErrorBox, Loading } from "@/components/common";
import { Upload } from "@/components/resumes/upload";
import { ResumeTable } from "@/components/resumes/table";
import type { Resume } from "@/types/api";
export default function Page() {
  const { data, error, isPending } = useQuery({
    queryKey: ["resumes"],
    queryFn: () => api<Resume[]>("/resumes"),
    refetchInterval: 4000,
  });
  return (
    <>
      <Heading title="My resumes" subtitle="Private documents. Real qualifications. Always editable." />
      <div className="stack">
        <section className="panel">
          <Upload />
        </section>
        <section className="panel">
          {isPending ? (
            <Loading />
          ) : error ? (
            <ErrorBox error={error} />
          ) : (
            <ResumeTable resumes={data || []} />
          )}
        </section>
      </div>
    </>
  );
}
