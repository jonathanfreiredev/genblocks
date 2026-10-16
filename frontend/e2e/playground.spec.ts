import { expect, test } from "@playwright/test";

/**
 * The playground section only needs the frontend to render. The run itself talks
 * to the backend and then to the MCP server, so exercising it belongs to a stack
 * that is up, not to this suite.
 */
test("the landing renders the playground section", async ({ page }) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { name: "Run it here", level: 2 }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Run the agent" }),
  ).toBeVisible();
});
