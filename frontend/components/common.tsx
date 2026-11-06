"use client";
import { Search, Sparkles, ShieldCheck, LoaderCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { User } from "@/types/api";

export function useUser() {
  return useQuery({ queryKey: ["me"], queryFn: () => api<User>("/auth/me") });
}
export function Brand() {
  return (
    <Link href="/" className="brand" aria-label="TalentLens AI home">
      <span className="brand-mark">
        <Sparkles size={20} />
      </span>
      TalentLens <em>AI</em>
    </Link>
  );
}
export function Empty({
  title,
  children,
  href,
  action,
}: {
  title: string;
  children: React.ReactNode;
  href?: string;
  action?: string;
}) {
  return (
    <div className="empty">
      <Search size={28} />
      <h3>{title}</h3>
      <p>{children}</p>
      {href && (
        <Button asChild size="sm">
          <Link href={href}>{action}</Link>
        </Button>
      )}
    </div>
  );
}
export function ErrorBox({ error }: { error: unknown }) {
  return error ? (
    <div className="error" role="alert">
      {error instanceof Error ? error.message : "Something went wrong. Please retry."}
    </div>
  ) : null;
}
export function Loading() {
  return (
    <div className="stack" role="status" aria-label="Loading">
      <div className="skeleton" />
      <div className="skeleton" />
    </div>
  );
}
export function Pending({ children }: { children?: React.ReactNode }) {
  return (
    <span className="row">
      <LoaderCircle size={15} className="animate-spin" />
      {children || "Working…"}
    </span>
  );
}
export function ResponsibleNotice() {
  return (
    <div className="notice">
      <ShieldCheck size={16} />
      <span>
        Your qualifications, in context. Scores are heuristic relevance estimates, never hiring probabilities.
        Missing evidence does not mean a missing skill. People make the decisions.
      </span>
    </div>
  );
}
export function Status({ value }: { value: string }) {
  const kind = ["COMPLETED", "PUBLISHED", "SHORTLISTED"].includes(value)
    ? "green"
    : ["FAILED", "RETRYING"].includes(value)
      ? "amber"
      : "purple";
  return <span className={`pill ${kind}`}>{value.toLowerCase().replaceAll("_", " ")}</span>;
}
export function Heading({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        <p>{subtitle}</p>
      </div>
      {children}
    </div>
  );
}
export function dateLabel(value: string) {
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(
    new Date(value),
  );
}
