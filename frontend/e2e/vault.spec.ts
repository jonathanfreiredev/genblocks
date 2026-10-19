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

test("an item opens on its render with its evidence", async ({ page }) => {
  await page.goto("/");

  const cell = page.locator('[data-slot="item-cell"] a').first();
  const title = await cell.getByRole("heading").innerText();
  await cell.click();

  await expect(page).toHaveURL(/item=/);

  const dialog = page.getByRole("dialog");
  await expect(dialog).toBeVisible();
  await expect(dialog.getByRole("heading", { name: title })).toBeVisible();

  // The render is what somebody browsing came to see, so it is what the dialog
  // opens on, with the numbers already beside it.
  await expect(dialog.getByRole("tab", { name: "Render" })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  await expect(dialog.getByText("Judge")).toBeVisible();

  await page.keyboard.press("Escape");
  await expect(page).not.toHaveURL(/item=/);
});

test("the code is a tab away, with both columns open and both collapsible", async ({
  page,
}) => {
  await page.goto("/");

  const dialog = page.getByRole("dialog");
  const cells = page.locator('[data-slot="item-cell"] a');

  // Not every row is a project: the seeded ones are a single file. Walk the
  // sheet until one arrives with a file rail, rather than pinning a title that
  // the dataset will outgrow.
  let found = false;
  for (let index = 0; index < 10 && !found; index += 1) {
    await cells.nth(index).click();
    await expect(dialog).toBeVisible();
    await dialog.getByRole("tab", { name: "Code" }).click();

    found = (await dialog.getByRole("button", { name: /^src\// }).count()) > 0;

    if (!found) {
      await page.keyboard.press("Escape");
      await expect(page).not.toHaveURL(/item=/);
    }
  }

  expect(found).toBe(true);

  await expect(dialog.getByText("Judge")).toBeVisible();

  // Each column can go away on its own: one reader wants the file wide, another
  // wants the numbers and nothing else.
  await dialog.getByRole("button", { name: "Hide the files" }).click();
  await expect(dialog.getByRole("button", { name: /^src\// })).toHaveCount(0);
  await expect(dialog.getByText("Judge")).toBeVisible();

  await dialog.getByRole("button", { name: "Show the files" }).click();
  await expect(dialog.getByRole("button", { name: /^src\// })).toBeVisible();

  await dialog.getByRole("button", { name: "Hide the scores" }).click();
  await expect(dialog.getByText("Judge")).toHaveCount(0);
  await expect(dialog.getByRole("button", { name: /^src\// })).toBeVisible();
});

test("images wait for their asset rather than breaking", async ({ page }) => {
  await page.goto("/?kind=image");

  await expect(page.locator('[data-slot="item-cell"]').first()).toBeVisible();
  await expect(page.getByText("Awaiting asset").first()).toBeVisible();
});
