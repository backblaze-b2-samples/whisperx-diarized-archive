import { test, expect } from "@playwright/test";

test.describe("Navigation", () => {
  test("should display the upload page", async ({ page }) => {
    await page.goto("/upload");
    await expect(page).toHaveURL(/upload/);
  });

  test("should navigate to files page", async ({ page }) => {
    await page.goto("/files");
    await expect(page).toHaveURL(/files/);
  });

  test("should navigate to the library page", async ({ page }) => {
    await page.goto("/library");
    await expect(page).toHaveURL(/library/);
  });

  test("should navigate to the search page", async ({ page }) => {
    await page.goto("/search");
    await expect(page).toHaveURL(/search/);
  });

  test("should display the dashboard", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("body")).toBeVisible();
  });
});
