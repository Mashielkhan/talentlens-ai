import { test, expect } from "@playwright/test";
import path from "node:path";
test("real applicant and recruiter journey", async ({ browser }) => {
  test.skip(
    process.env.RUN_FULL_E2E !== "1",
    "Requires PostgreSQL, Redis, model worker and scripts/generate-demo.py fixtures",
  );
  const applicantContext = await browser.newContext(),
    recruiterContext = await browser.newContext();
  const applicant = await applicantContext.newPage(),
    recruiter = await recruiterContext.newPage();
  const pageErrors: string[] = [];
  for (const page of [applicant, recruiter]) page.on("pageerror", (error) => pageErrors.push(error.message));
  const suffix = Date.now();
  for (const [page, role] of [
    [recruiter, "recruiter"],
    [applicant, "applicant"],
  ] as const) {
    await page.goto("/register");
    if (role === "recruiter") {
      await page.getByRole("button", { name: "I’m hiring" }).click();
      await page.getByLabel("Company name").fill("Synthetic E2E Company");
    }
    await page.getByLabel("Full name").fill(`Synthetic ${role}`);
    await page.getByLabel("Email address").fill(`${role}-${suffix}@example.org`);
    await page.getByLabel("Password", { exact: true }).fill("Synthetic-E2E-Password-2048!");
    await page.getByLabel("Confirm password").fill("Synthetic-E2E-Password-2048!");
    await page.getByRole("button", { name: "Create account", exact: true }).click();
    await expect(page.getByRole("heading", { name: "Overview", exact: true })).toBeVisible();
  }
  await recruiter.goto("/jobs/new");
  await recruiter.getByLabel("Job title").fill("Synthetic Python Backend Engineer");
  await recruiter.getByLabel("Company", { exact: true }).fill("Synthetic E2E Company");
  await recruiter
    .getByLabel("Responsibilities & qualifications")
    .fill("Build Python backend REST APIs using FastAPI and PostgreSQL with Docker containers.");
  await recruiter.getByLabel(/Required skills/).fill("Python:5, FastAPI:4, PostgreSQL:3");
  await recruiter.getByLabel("Visibility").selectOption("PUBLISHED");
  await recruiter.getByRole("button", { name: "Save job" }).click();
  await expect(
    recruiter.getByRole("alert").filter({ hasText: "Review and confirm requirements" }),
  ).toBeVisible();
  await expect(recruiter.getByLabel("Job title")).toHaveValue("Synthetic Python Backend Engineer");
  await expect(recruiter.getByLabel(/Required skills/)).toHaveValue("Python:5, FastAPI:4, PostgreSQL:3");
  await recruiter.getByLabel(/I reviewed these requirements/).check();
  await recruiter.getByRole("button", { name: "Save job" }).click();
  await expect(recruiter).toHaveURL(/\/jobs\/[a-f0-9-]+$/);
  const jobUrl = recruiter.url();
  await applicant.goto("/resumes");
  await applicant
    .getByLabel("Resume file")
    .setInputFiles(path.resolve("../ml/datasets/generated/synthetic-01.pdf"));
  await expect(applicant.getByText("completed", { exact: true }).first()).toBeVisible({ timeout: 150000 });
  await applicant.goto(jobUrl);
  const selector = applicant.getByLabel("Choose a processed resume");
  await expect(selector.locator("option")).toHaveCount(2);
  await selector.selectOption({ index: 1 });
  await applicant.getByRole("button", { name: "Analyze privately" }).click();
  await expect(applicant.getByRole("link", { name: "View analysis", exact: true })).toBeVisible({
    timeout: 150000,
  });
  await applicant.getByLabel(/I consent to share/).check();
  await applicant.getByRole("button", { name: "Submit application" }).click();
  await expect(applicant.getByRole("button", { name: "Application submitted" })).toBeVisible();
  await recruiter.getByRole("button", { name: "Analyze applicants" }).click();
  await expect(recruiter.getByRole("link", { name: "View analysis", exact: true })).toBeVisible({
    timeout: 150000,
  });
  await applicant.getByRole("link", { name: "View analysis", exact: true }).click();
  await expect(applicant.getByText("Compatibility Index", { exact: true })).toBeVisible();
  const download = applicant.waitForEvent("download");
  await applicant.getByRole("link", { name: "Download PDF" }).click();
  expect((await download).suggestedFilename()).toMatch(/\.pdf$/);
  await applicant.goto("/studio");
  await applicant.getByLabel("Processed resume").selectOption({ index: 1 });
  await applicant.getByLabel("Draft title").fill("Synthetic beta CV");
  await applicant
    .getByLabel("Target job description")
    .fill("Build Python backend REST APIs using FastAPI and PostgreSQL with Docker containers.");
  await applicant.getByRole("button", { name: "Create CV draft" }).click();
  await expect(applicant).toHaveURL(/\/studio\/[a-f0-9-]+$/);
  await applicant.getByLabel("Full name", { exact: true }).fill("Synthetic Beta Applicant");
  await applicant
    .getByLabel("Summary", { exact: true })
    .fill("Python developer with documented FastAPI and PostgreSQL project experience.");
  await applicant.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(applicant.getByText(/Revision 2 ·/)).toBeVisible();
  await expect(applicant.getByRole("button", { name: "Save draft", exact: true })).toBeDisabled();
  await applicant.reload();
  await expect(applicant.getByLabel("Full name", { exact: true })).toHaveValue("Synthetic Beta Applicant");
  await applicant.getByLabel(/I reviewed this saved revision/).check();
  await applicant.getByRole("button", { name: "Approve this revision" }).click();
  for (const format of ["PDF", "DOCX"]) {
    const exported = applicant.waitForEvent("download");
    await applicant.getByRole("link", { name: `Download CV ${format}`, exact: true }).click();
    const file = await exported;
    expect(file.suggestedFilename()).toBe(`talentlens-cv.${format.toLowerCase()}`);
    expect(await file.failure()).toBeNull();
  }
  await applicant.getByLabel("Summary", { exact: true }).fill("An updated summary awaiting factual review.");
  await expect(applicant.getByRole("link", { name: "Download CV PDF", exact: true })).toHaveCount(0);
  await applicant.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(applicant.getByText(/Revision 3 ·/)).toBeVisible();
  await expect(applicant.getByRole("button", { name: "Save draft", exact: true })).toBeDisabled();
  await applicant.reload();
  await expect(applicant.getByRole("link", { name: "Download CV PDF", exact: true })).toHaveCount(0);
  const draftUrl = applicant.url();
  await applicant.goto("/resumes");
  await applicant.getByRole("link", { name: /Review synthetic-01/ }).click();
  await applicant.getByRole("button", { name: "Correct extraction", exact: true }).click();
  await applicant.getByLabel("name", { exact: true }).fill("Synthetic Corrected Applicant");
  await applicant
    .getByLabel("summary", { exact: true })
    .fill("A corrected synthetic summary describing Python API work.");
  await applicant.route(
    "**/api/v1/resumes/*",
    (route) =>
      route.request().method() === "PATCH"
        ? route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Synthetic correction failure" }),
          })
        : route.continue(),
    { times: 1 },
  );
  await applicant.getByRole("button", { name: "Save and reprocess" }).click();
  await expect(
    applicant.getByRole("alert").filter({ hasText: "Synthetic correction failure" }),
  ).toBeVisible();
  await expect(applicant.getByLabel("name", { exact: true })).toHaveValue("Synthetic Corrected Applicant");
  await expect(applicant.getByLabel("summary", { exact: true })).toHaveValue(
    "A corrected synthetic summary describing Python API work.",
  );
  await applicant.getByRole("button", { name: "Save and reprocess" }).click();
  await expect(applicant.getByText(/Version 2 ·/)).toBeVisible();
  await expect(applicant.getByText("completed", { exact: true })).toBeVisible({ timeout: 150000 });
  await expect(applicant.getByText("Synthetic Corrected Applicant", { exact: true })).toBeVisible();
  await applicant.goto(draftUrl);
  await expect(applicant.getByRole("alert").filter({ hasText: "original resume changed" })).toBeVisible();
  await expect(applicant.getByLabel("Full name", { exact: true })).toBeDisabled();
  applicant.once("dialog", (dialog) => dialog.accept());
  await applicant.getByRole("button", { name: "Delete draft", exact: true }).click();
  await expect(applicant).toHaveURL(/\/studio$/);
  await applicant.goto("/feedback");
  await applicant
    .getByLabel("Your feedback")
    .fill("Synthetic browser check: CV Studio export completed successfully.");
  await applicant.getByRole("button", { name: "Send feedback" }).click();
  await expect(applicant.getByRole("status")).toContainText("feedback has been saved");
  await applicant.goto("/resumes");
  await applicant.getByRole("link", { name: /Review synthetic-01/ }).click();
  applicant.once("dialog", (dialog) => dialog.accept());
  await applicant.getByRole("button", { name: "Delete", exact: true }).click();
  await expect(applicant).toHaveURL(/\/resumes$/);
  expect(pageErrors).toEqual([]);
  await applicantContext.close();
  await recruiterContext.close();
});
