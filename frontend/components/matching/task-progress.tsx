"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";
import { ErrorBox, Status } from "@/components/common";
import { Button } from "@/components/ui/button";
import type { Task } from "@/types/api";
export function TaskProgress({ id }: { id: string }) {
  const { data, error } = useQuery({
    queryKey: ["task", id],
    queryFn: () => api<Task>(`/tasks/${id}`),
    refetchInterval: (q) => (["COMPLETED", "FAILED"].includes(q.state.data?.status || "") ? false : 2000),
  });
  return (
    <div className="panel">
      <ErrorBox error={error} />
      <div className="row between">
        <h3 className="mb-0">Qualification analysis</h3>
        <Status value={data?.status || "PENDING"} />
      </div>
      <div className="bar">
        <span style={{ width: `${data?.progress || 3}%` }} />
      </div>
      {data?.status === "FAILED" ? (
        <p className="error mt-3">{data.error_code}. Check the worker, review inputs, and run again.</p>
      ) : data?.status === "COMPLETED" ? (
        <div className="mt-4">
          {data.result.match_ids?.length ? (
            <Button asChild size="sm">
              <Link
                href={
                  data.result.match_ids.length === 1 ? `/matches/${data.result.match_ids[0]}` : "/matches"
                }
              >
                View analysis
              </Link>
            </Button>
          ) : (
            <p className="muted text-xs mb-0">No ready, consented applicants were available for this run.</p>
          )}
        </div>
      ) : (
        <p className="muted text-xs mt-3 mb-0">
          Processing in the background. This panel updates automatically.
        </p>
      )}
    </div>
  );
}
