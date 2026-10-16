import { expect, test } from "@playwright/test";

test("home page renders", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("main").getByRole("heading", { name: "MCPStack" }),
  ).toBeVisible();
});

test("login page renders the form", async ({ page }) => {
  await page.goto("/auth/login");

  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Log in" })).toBeVisible();
});

test("protected route redirects unauthenticated users to login", async ({
  page,
}) => {
  await page.goto("/profile");

  await expect(page).toHaveURL(/\/auth\/login$/);
});
