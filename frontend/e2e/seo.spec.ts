import { expect, test } from "@playwright/test";

/**
 * The crawl and share surface.
 *
 * These are the files a search engine or a social card reads before it ever
 * renders the app, so they are checked directly rather than through the shell.
 */

test("robots.txt names the sitemap and closes private surfaces", async ({
  request,
}) => {
  const response = await request.get("/robots.txt");

  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("text/plain");

  const body = await response.text();
  expect(body).toContain("Sitemap:");
  for (const path of [
    "/tasks",
    "/profile",
    "/admin",
    "/auth",
    "/oauth",
    "/api",
  ]) {
    expect(body).toContain(`Disallow: ${path}`);
  }
});

test("the sitemap carries public pages and never private ones", async ({
  request,
}) => {
  const response = await request.get("/sitemap.xml");

  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("xml");

  const body = await response.text();
  expect(body).toContain("/blocks");
  expect(body).toContain("/images");
  expect(body).toContain("/about");
  expect(body).toContain("/privacy");
  expect(body).toContain("/mcp");

  for (const path of ["/tasks", "/profile", "/admin", "/auth", "/oauth"]) {
    expect(body).not.toContain(path);
  }
});

test("the web manifest is installable and points at the catalogue", async ({
  request,
}) => {
  const response = await request.get("/manifest.webmanifest");

  expect(response.status()).toBe(200);
  const manifest = (await response.json()) as {
    name: string;
    start_url: string;
    icons: { src: string; sizes: string }[];
  };

  expect(manifest.name).toContain("GenBlocks");
  expect(manifest.start_url).toBe("/blocks");
  expect(manifest.icons).toEqual(
    expect.arrayContaining([
      expect.objectContaining({ sizes: "192x192" }),
      expect.objectContaining({ sizes: "512x512" }),
    ]),
  );
});

test("a public page carries a canonical, an indexable robots tag and an OG image", async ({
  page,
  request,
}) => {
  await page.goto("/about");

  expect(await page.title()).toContain("GenBlocks");

  const canonical = await page
    .locator('link[rel="canonical"]')
    .getAttribute("href");
  expect(canonical).not.toBeNull();
  expect(new URL(canonical!).pathname).toBe("/about");

  await expect(page.locator('meta[name="robots"]')).toHaveAttribute(
    "content",
    /index, follow/,
  );

  const image = await page
    .locator('meta[property="og:image"]')
    .getAttribute("content");
  expect(image).not.toBeNull();

  // The card URL is absolute in production metadata. Fetch its path from the
  // local server so this test does not depend on the environment's origin.
  const card = new URL(image!);
  const response = await request.get(`${card.pathname}${card.search}`);
  expect(response.status()).toBe(200);
  expect(response.headers()["content-type"]).toContain("image/png");

  // A PNG stores its dimensions at bytes 16 and 20.
  const bytes = await response.body();
  expect(bytes.readUInt32BE(16)).toBe(1200);
  expect(bytes.readUInt32BE(20)).toBe(630);
});

test("an account surface is noindex at the transport and in the document", async ({
  request,
}) => {
  const response = await request.get("/auth/login");

  expect(response.status()).toBe(200);
  expect(response.headers()["x-robots-tag"]).toContain("noindex");
  expect(await response.text()).toContain("noindex");
});

test("the front page redirects permanently to the catalogue", async ({
  request,
}) => {
  const response = await request.get("/", { maxRedirects: 0 });

  expect(response.status()).toBe(308);
  expect(response.headers()["location"]).toContain("/blocks");
});
