"use client";
import { use } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ErrorBox, Loading } from "@/components/common";
import { CvEditor } from "@/components/cv-editor";
import type { CvDraft } from "@/types/api";

export default function DraftPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const query = useQuery({
    queryKey: ["cv-draft", id],
    queryFn: () => api<CvDraft>(`/studio/${id}`),
    refetchOnWindowFocus: false,
  });
  if (query.isPending) return <Loading />;
  if (!query.data) return <ErrorBox error={query.error} />;
  return <CvEditor key={`${id}:${query.data.revision}`} draft={query.data} />;
}
