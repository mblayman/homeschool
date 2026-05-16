const { test, expect } = require("@playwright/test");

test("public index page loads", async ({ page }) => {
  const response = await page.goto("/");

  expect(response).not.toBeNull();
  expect(response.ok()).toBeTruthy();
  await expect(page.locator("body")).toBeVisible();
});

test("staff user can log in via admin", async ({ page }) => {
  await page.goto("/office/login/");

  await page.getByLabel("Username:").fill("e2e-admin");
  await page.getByLabel("Password:").fill("e2e-password");
  await page.getByRole("button", { name: "Log in" }).click();

  await expect(page).toHaveURL(/\/office\/$/);
  await expect(page.getByRole("button", { name: "Log out" })).toBeVisible();
});
