import { expect, test } from "@playwright/test";

/**
 * The vault against the development dataset.
 *
 * These need the whole local stack and the seeded rows:
 *
 *   docker compose up
 *   docker compose run --rm --no-deps backend python -m app.seed.vault
 */

test("the wall files what it holds", async ({ page }) => {
  await page.goto("/blocks");

  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();
  await expect(page.getByText(/^\d+ blocks$/)).toBeVisible();
});

test("a type narrows the wall from the sidebar", async ({ page }) => {
  await page.goto("/blocks");

  const shown = async () =>
    Number((await page.getByText(/^\d+ blocks$/).innerText()).split(" ")[0]);

  const all = await shown();

  await page.getByRole("link", { name: "Hero", exact: true }).click();

  await expect(page).toHaveURL(/\/blocks\/hero$/);
  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();

  // Narrowed, not counted: the dataset grows every time somebody builds a block,
  // and a test that pinned the number would fail the day the registry did the
  // thing it exists for.
  expect(await shown()).toBeLessThan(all);
});

test("an item opens as a page on its render", async ({ page }) => {
  await page.goto("/blocks");

  const cell = page.locator('[data-slot="item-cell"] a').first();
  const title = await cell.getAttribute("aria-label");
  await cell.click();

  await expect(page).toHaveURL(/\/blocks\/[0-9a-f-]{36}$/);
  await expect(
    page.getByRole("heading", { level: 1, name: title ?? "" }),
  ).toBeVisible();

  // The render is above the tabs, not behind one of them.
  await expect(page.getByRole("tab", { name: "render" })).toHaveCount(0);
  await expect(page.getByRole("tab", { name: "code" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "prompt" })).toBeVisible();
  await expect(page.getByText("Judge")).toBeVisible();
});

test("code and prompt swap on the left while the evidence stays", async ({
  page,
}) => {
  await page.goto("/blocks");

  await page.locator('[data-slot="item-cell"] a').first().click();

  await page.getByRole("tab", { name: "code" }).click();
  await expect(page.locator("pre")).toBeVisible();

  await page.getByRole("tab", { name: "prompt" }).click();
  await expect(page.getByRole("tab", { name: "prompt" })).toHaveAttribute(
    "aria-selected",
    "true",
  );

  // The right column is a column, not a tab: the numbers do not go away when
  // the reader looks at the words.
  await expect(page.getByText("Judge")).toBeVisible();
});

test("the project's files stay visible and collapse", async ({ page }) => {
  await page.goto("/blocks");

  await page.locator('[data-slot="item-cell"] a').first().click();
  await page.getByRole("tab", { name: "code" }).click();

  // The rail is part of the code view, not a reward for a multi-file project.
  await expect(page.getByText("Files", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Hide the files" }).click();
  await page.getByRole("button", { name: "Show the files" }).click();

  await expect(page.getByText("Files", { exact: true })).toBeVisible();
});

test("an image whose asset cannot arrive says so rather than breaking", async ({
  page,
}) => {
  // The rows have real assets, so the fallback is exercised the only way it
  // happens in production: the delivery fails.
  await page.route("**/_next/image**", (route) => route.abort());

  await page.goto("/images");

  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();
  await expect(page.getByText("Awaiting asset").first()).toBeVisible();
});

test("search lands on a filtered wall", async ({ page }) => {
  await page.goto("/blocks");

  await page.getByRole("button", { name: "search" }).first().click();

  const dialog = page.getByRole("dialog");
  await dialog.getByRole("textbox").fill("hero");
  await dialog.getByRole("textbox").press("Enter");

  await expect(page).toHaveURL(/\/blocks\?q=hero$/);
  await expect(page.getByText(/for “hero”/)).toBeVisible();
});
