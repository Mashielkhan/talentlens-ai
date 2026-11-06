"use client";
import { use } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ErrorBox, Heading, Loading } from "@/components/common";
import { MatchView } from "@/components/matching/result";
import type { Match } from "@/types/api";
export default function Page({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const query = useQuery({ queryKey: ["match", id], queryFn: () => api<Match>(`/matches/${id}`) });
  return (
    <>
      <Link href="/matches" className="text-link">
        ← All analyses
      </Link>
      <Heading
        title="A closer look at the match"
        subtitle="Trace every score back to documented qualifications."
      />
      {query.isPending ? (
        <Loading />
      ) : query.error || !query.data ? (
        <ErrorBox error={query.error} />
      ) : (
        <MatchView match={query.data} />
      )}
    </>
  );
}
