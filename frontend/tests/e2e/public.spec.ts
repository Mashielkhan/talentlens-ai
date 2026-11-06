import { test, expect } from "@playwright/test";
test("landing and registration are accessible on desktop and mobile", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Beyond keywords/ })).toBeVisible();
  await page.getByRole("link", { name: "Get started" }).click();
  await expect(page.getByRole("heading", { name: "Create your workspace" })).toBeVisible();
  await page.getByRole("button", { name: "I’m hiring" }).click();
  await expect(page.getByLabel("Company name")).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBeTruthy();
});
