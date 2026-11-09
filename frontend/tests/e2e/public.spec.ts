import { test, expect } from "@playwright/test";
test("landing and registration are accessible on desktop and mobile", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Beyond keywords/ })).toBeVisible();
  await page.getByRole("link", { name: "Get started" }).click();
  await expect(page.getByRole("heading", { name: "Create your workspace" })).toBeVisible();
  await page.getByRole("button", { name: "I’m hiring" }).click();
  await expect(page.getByLabel("Company name")).toBeVisible();
  await page.getByRole("button", { name: "Create account", exact: true }).click();
  await expect(page.getByText("Enter a valid email address", { exact: true })).toBeVisible();
  await page.getByLabel("Email address", { exact: true }).fill("synthetic-validation@example.org");
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});
