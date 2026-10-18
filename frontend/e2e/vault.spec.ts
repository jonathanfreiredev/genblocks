import { expect, test } from "@playwright/test";

/**
 * The vault against the development dataset.
 *
 * These need the whole local stack and the seeded rows:
 *
 *   docker compose up
 *   docker compose run --rm --no-deps backend python -m app.seed.vault
 */

test("the gallery files what it holds", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();
  await expect(page.getByText(/^\d+ blocks$/)).toBeVisible();
});

test("a type narrows the sheet", async ({ page }) => {
  await page.goto("/");

  const shown = () =>
    page
      .getByText(/^\d+ blocks$/)
      .innerText()
      .then((said) => Number(said.split(" ")[0]));

  const all = await shown();

  await page.getByRole("link", { name: "Hero", exact: true }).click();

  await expect(page).toHaveURL(/type=hero/);
  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();

  // Narrowed, not counted: the dataset grows every time somebody builds a block,
  // and a test that pinned the number would fail the day the registry did the
  // thing it exists for.
  expect(await shown()).toBeLessThan(all);
});

test("an item opens with its code and its evidence", async ({ page }) => {
  await page.goto("/");

  const cell = page.locator('[data-slot="item-cell"] a').first();
  const title = await cell.getByRole("heading").innerText();
  await cell.click();

  await expect(page).toHaveURL(/item=/);

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: title })).toBeVisible();
  await expect(dialog.getByRole("tab", { name: "Code" })).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page).not.toHaveURL(/item=/);
});

test("images wait for their asset rather than breaking", async ({ page }) => {
  await page.goto("/?kind=image");

  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();
  await expect(page.getByText("Awaiting asset").first()).toBeVisible();
});
