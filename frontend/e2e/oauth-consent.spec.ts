import { expect, test } from "@playwright/test";

test("consent screen asks for an authorization id", async ({ page }) => {
  await page.goto("/oauth/consent");

  await expect(page.getByText("Cannot continue")).toBeVisible();
  await expect(page.getByText(/missing its authorization id/)).toBeVisible();
});

test("consent screen sends an anonymous visitor to log in, and back", async ({
  page,
}) => {
  await page.goto("/oauth/consent?authorization_id=test-id");

  // The flow has to survive the login detour: the authorization id rides in
  // `next`, and the login form returns to it.
  await expect(page).toHaveURL(/\/auth\/login\?next=/);
  expect(new URL(page.url()).searchParams.get("next")).toBe(
    "/oauth/consent?authorization_id=test-id",
  );
  await expect(page.getByRole("button", { name: "Log in" })).toBeVisible();
});
