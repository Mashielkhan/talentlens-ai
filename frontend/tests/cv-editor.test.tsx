import { fireEvent, render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, expect, it, vi } from "vitest";
import { CvEditor } from "@/components/cv-editor";
import type { CvContent, CvDraft } from "@/types/api";

vi.mock("next/navigation", () => ({ useRouter: () => ({ push: vi.fn() }) }));
const content: CvContent = {
  name: "Synthetic Person",
  email: "",
  phone: "",
  links: "",
  summary: "",
  skills: "Python",
  experience: "I built a tool.",
  education: "",
  projects: "",
  certifications: "",
};
const draft: CvDraft = {
  id: "draft",
  resume_id: "resume",
  source_version: 1,
  source_outdated: false,
  title: "Synthetic draft",
  target_description: "Build a Python application.",
  original: content,
  content,
  revision: 1,
  approved_revision: 1,
  created_at: "2026-11-08",
  guidance: {
    method: "rules",
    prompts: [],
    documented_target_skills: ["Python"],
    not_documented_target_skills: ["Docker"],
    suggestions: [
      {
        id: 0,
        section: "experience",
        original: "I built a tool.",
        replacement: "Built a tool.",
        reason: "Concise wording",
      },
    ],
  },
};
function show(value = draft) {
  render(
    <QueryClientProvider client={new QueryClient()}>
      <CvEditor draft={value} />
    </QueryClientProvider>,
  );
}

describe("CV draft review", () => {
  it("never applies a suggestion automatically and hides exports after an edit", () => {
    show();
    expect(screen.getByLabelText("Experience")).toHaveValue("I built a tool.");
    expect(screen.getByRole("link", { name: "Download CV PDF" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Use this wording" }));
    expect(screen.getByLabelText("Experience")).toHaveValue("Built a tool.");
    expect(screen.queryByRole("link", { name: "Download CV PDF" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Approve this revision" })).toBeDisabled();
    expect(screen.getByLabelText("Skills")).toHaveValue("Python");
  });
  it("blocks editing and export when the source changed", () => {
    show({ ...draft, source_outdated: true });
    expect(screen.getByLabelText("Experience")).toBeDisabled();
    expect(screen.queryByRole("link", { name: "Download CV PDF" })).not.toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("original resume changed");
  });
});
