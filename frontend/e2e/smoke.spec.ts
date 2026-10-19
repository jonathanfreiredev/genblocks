import { expect, test } from "@playwright/test";

/**
 * The vault's shell: headings, navigation and the one action.
 *
 * Only what is below "an item opens" needs data behind it; everything above
 * holds whether or not an API is answering, which is the point of the page
 * rendering its own frame before it reads anything.
 */
test("home page opens on the blocks", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("main").getByRole("heading", { level: 1 }),
  ).toHaveText("Blocks");
});

test("the kinds swap the sheet", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("link", { name: "Images", exact: true }).click();

  await expect(page).toHaveURL(/kind=image/);
  await expect(
    page.getByRole("main").getByRole("heading", { level: 1 }),
  ).toHaveText("Images");
});

test("the generator dialog opens and asks a visitor to sign in", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Generate with AI" }).click();

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
