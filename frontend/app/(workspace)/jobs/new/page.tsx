"use client";
import { Heading, useUser } from "@/components/common";
import { JobForm } from "@/components/jobs/job-form";
export default function Page() {
  const { data: user } = useUser();
  return (
    <>
      <Heading
        title="Create an opportunity"
        subtitle="Define the work, review the criteria, and keep the decision human."
      />
      <JobForm company={user?.profile.company} />
    </>
  );
}
