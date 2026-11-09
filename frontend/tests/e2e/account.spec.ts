import { test, expect } from "@playwright/test";

test("account edits survive errors, password changes and mobile navigation work", async ({ page }) => {
  test.skip(process.env.RUN_FULL_E2E !== "1", "Requires the running API and database");
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const email = `account-check-${Date.now()}@example.org`;
  const password = "Synthetic-Account-Password-2048!";
  const changedPassword = "Synthetic-Changed-Password-2048!";
  await page.goto("/register");
  await page.getByLabel("Full name", { exact: true }).fill("Synthetic Account Check");
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto("/settings");
  await page.getByLabel("Full name", { exact: true }).fill("Synthetic Updated Person");
  await page.getByLabel("About you", { exact: true }).fill("A synthetic biography to preserve.");
  await page.route(
    "**/api/v1/auth/profile",
    (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Synthetic temporary failure" }),
      }),
    { times: 1 },
  );
  await page.getByRole("button", { name: "Save profile", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Synthetic temporary failure" })).toBeVisible();
  await expect(page.getByLabel("Full name", { exact: true })).toHaveValue("Synthetic Updated Person");
  await expect(page.getByLabel("About you", { exact: true })).toHaveValue(
    "A synthetic biography to preserve.",
  );
  await page.getByRole("button", { name: "Save profile", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Changes saved");
  await page.reload();
  await expect(page.getByLabel("About you", { exact: true })).toHaveValue(
    "A synthetic biography to preserve.",
  );
  await page.getByLabel("About you", { exact: true }).fill("A second saved biography.");
  await page.getByRole("button", { name: "Save profile", exact: true }).click();
  await expect(page.getByRole("status")).toContainText("Changes saved");
  await page.getByLabel("Current password", { exact: true }).fill(password);
  await page.getByLabel("New password", { exact: true }).fill(changedPassword);
  const changed = page.waitForResponse((r) => r.url().endsWith("/auth/password") && r.status() === 204);
  await page.getByRole("button", { name: "Update password", exact: true }).click();
  await changed;
  await page.setViewportSize({ width: 390, height: 667 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page
    .getByRole("navigation", { name: "Main navigation" })
    .getByRole("link", { name: "Account access", exact: true })
    .click();
  await expect(page.getByRole("heading", { name: "Account access", exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page.getByRole("alert").filter({ hasText: "Email or password is incorrect" })).toBeVisible();
  await page.getByLabel("Password", { exact: true }).fill(changedPassword);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(page).toHaveURL(/\/dashboard$/);
  await page.goto("/settings");
  await expect(page.getByLabel("About you", { exact: true })).toHaveValue("A second saved biography.");
  await page.getByLabel("Confirm your password").fill(changedPassword);
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Delete my account and data" }).click();
  await expect(page).toHaveURL(/\/$/);
  expect(errors).toEqual([]);
});
