/**
 * The one place the product's public identity is written down.
 *
 * Metadata, the sitemap, robots, the manifest and the social cards all read
 * from here. `SITE_URL` is the canonical origin in production; the fallback is
 * the address the product is actually served from, so a build without the
 * variable still emits absolute URLs instead of failing.
 */
const FALLBACK_ORIGIN = "https://genblocks.jonathanfreire.com";

export const SITE_NAME = "GenBlocks";
export const SITE_TITLE =
  "GenBlocks — Generated UI blocks and stock images, scored";
export const SITE_DESCRIPTION =
  "Browse generated UI blocks and stock images, each scored by an independent judge. Copy the code, inspect the evidence, or connect an agent over MCP.";
export const SITE_LOCALE = "en_US";
export const SITE_AUTHOR = {
  name: "Jonathan Freire",
  url: "https://jonathanfreire.com",
} as const;

export const SITE_ORIGIN = (
  process.env.SITE_URL?.trim() || FALLBACK_ORIGIN
).replace(/\/+$/, "");

/** An absolute URL for a path, safe to put in metadata or JSON-LD. */
export function absoluteUrl(path = "/"): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }

  return `${SITE_ORIGIN}${path.startsWith("/") ? path : `/${path}`}`;
}

/** The canonical path for a page, with a single leading slash. */
export function canonicalPath(path: string): string {
  return path.startsWith("/") ? path : `/${path}`;
}
