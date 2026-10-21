/**
 * The policy a block's built page is served with.
 *
 * The document is generated code, so it is treated as untrusted even though the
 * bundle was scanned: `sandbox allow-scripts allow-forms` puts it on an opaque
 * origin, which is what keeps it away from the session, the storage and the DOM
 * of the page that embeds it. `allow-same-origin` is deliberately absent — adding
 * it would undo the whole thing.
 *
 * Forms are allowed to *fire* and not to *send*: a visitor testing a block needs
 * the `submit` handler (that is where validation lives), and `form-action 'none'`
 * is what stops the request it would otherwise make.
 *
 * The rest closes what a page can reach: no network, no nested frames, no external
 * styles. Pictures from Cloudinary are the one thing a block is allowed to load,
 * because a block's stock image lives there.
 *
 * This policy is repeated as a `<meta>` inside the document (see the scaffold's
 * `scripts/inline.mjs`). Two policies do not weaken each other: a browser
 * enforces the intersection, so a document that lost the header still cannot
 * reach the network, and a document that lost the meta still cannot reach this
 * origin.
 */
export const PREVIEW_CSP = [
  "sandbox allow-scripts allow-forms",
  "default-src 'none'",
  "script-src 'unsafe-inline'",
  "style-src 'unsafe-inline'",
  "img-src https://res.cloudinary.com data:",
  "font-src data:",
  "connect-src 'none'",
  "form-action 'none'",
  "frame-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
  "frame-ancestors 'self'",
].join("; ");

/** The address the item view embeds. */
export function previewUrl(
  componentId: string,
  theme: "light" | "dark",
): string {
  return `/api/previews/${componentId}?theme=${theme}`;
}
