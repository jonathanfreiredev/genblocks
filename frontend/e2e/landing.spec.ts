import { expect, test } from "@playwright/test";

test("the hero command reaches the clipboard", async ({ page, context }) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");

  await page.getByRole("button", { name: "Copy the commands" }).click();

  await expect(page.getByRole("button", { name: "Copied" })).toBeVisible();

  const clipboard = await page.evaluate(() => navigator.clipboard.readText());
  expect(clipboard).toContain("docker compose up");
});

test("the connect section swaps the snippet with the chosen client", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "Cursor", exact: true }).click();
  const cursorPanel = page.getByRole("group", { name: "Cursor setup" });
  await expect(cursorPanel.locator("pre")).toContainText("mcpServers");

  await page.getByRole("button", { name: "n8n", exact: true }).click();
  const n8nPanel = page.getByRole("group", { name: "n8n setup" });
  await expect(n8nPanel.locator("pre")).toHaveText(
    "http://localhost:8001/mcp",
  );
});
