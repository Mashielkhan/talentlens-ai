import React from "react";
import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { MatchView } from "@/components/matching/result";
import type { Match } from "@/types/api";
it("shows unknown components, evidence gaps and the hiring disclaimer", () => {
  const match = {
    id: "test",
    compatibility_index: 60,
    resume_filename: "Synthetic.pdf",
    job_title: "Backend role",
    score_breakdown: { semantic_relevance: 60, experience: null },
    effective_weights: { semantic_relevance: 1, experience: 0 },
    matched_skills: ["Python"],
    not_documented_required_skills: ["Docker"],
    not_documented_preferred_skills: [],
    evidence: [],
    relevant_experience_months: null,
    education_evidence: "",
    uncertainties: ["Dates unknown"],
    recommendations: [],
    disclaimer: "Not a hiring probability. Human review is required.",
    created_at: "2026-01-01T00:00:00Z",
    as_of_date: "2026-01-01",
    model_version: "unit-test",
    scoring_version: "unit-test",
  } as unknown as Match;
  render(<MatchView match={match} />);
  expect(screen.getByText("Unknown / not applicable")).toBeInTheDocument();
  expect(screen.getByText("Docker")).toBeInTheDocument();
  expect(screen.getByText(/Not a hiring probability/)).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /Download PDF/ })).toHaveAttribute(
    "href",
    "/api/v1/reports/test/export",
  );
});
