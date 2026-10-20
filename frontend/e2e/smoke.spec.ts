import { expect, test } from "@playwright/test";

/**
 * The shell: where the app lands, how the two sections swap, and the one action.
 *
 * The gallery itself is covered in vault.spec.ts, which needs the seeded rows.
 * These hold with an empty vault too, which is the point of a shell that does not
 * wait for data to draw itself.
 */

test("the default route lands on the blocks", async ({ page }) => {
  await page.goto("/");

  await expect(page).toHaveURL(/\/blocks$/);
  await expect(
    page.getByRole("link", { name: "Blocks", exact: true }).first(),
  ).toBeVisible();
});

test("the sections swap from the sidebar", async ({ page }) => {
  await page.goto("/blocks");

  await page.getByRole("link", { name: "Images", exact: true }).first().click();

  await expect(page).toHaveURL(/\/images$/);
  await expect(
    page.getByRole("navigation", { name: "Breadcrumb" }).getByText("Images"),
  ).toBeVisible();
});

test("the search is a field in a dialog, opened from the header", async ({
  page,
}) => {
  await page.goto("/blocks");

  await page.getByRole("button", { name: "search" }).first().click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("textbox")).toBeVisible();
});

test("the assistant dialog opens and asks a visitor to sign in", async ({
  page,
}) => {
  await page.goto("/blocks");

  await page.getByRole("button", { name: "Ask AI" }).click();

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();

  // Queueing needs an account, because the task belongs to whoever asks for it.
  // A visitor gets the reason and the way in, not a field the guard would refuse
  // on the way out.
  await expect(dialog.getByText(/needs an account/)).toBeVisible();
  await expect(dialog.getByRole("link", { name: "Sign in" })).toBeVisible();
  await expect(dialog.getByLabel("Message")).toHaveCount(0);
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

test("your tasks redirects unauthenticated users to login", async ({
  page,
}) => {
  await page.goto("/tasks");

  await expect(page).toHaveURL(/\/auth\/login/);
});
