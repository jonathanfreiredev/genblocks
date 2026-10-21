/** A placeholder origin: anything parsed against it must stay on it. */
const BASE = "https://genblocks.invalid";

/**
 * Resolve a `next` search parameter to a path on this origin.
 *
 * A `next` value arrives in a URL, so it is attacker-controlled: redirecting to
 * it unchecked turns any page that honours it into an open redirect. Parsing it
 * against a fixed origin is what catches the forms a prefix check misses —
 * `/\evil.com`, `/%5cevil.com`, and a path that normalises back to `//host`.
 */
export function safeNextPath(
  value: string | null | undefined,
  fallback = "/",
): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return fallback;
  }

  // Reject the raw and percent-encoded backslash before a parser decides to
  // treat it as a path separator.
  if (/[\s\\]/.test(value) || /%5c/i.test(value)) {
    return fallback;
  }

  try {
    const parsed = new URL(value, BASE);
    if (parsed.origin !== BASE) {
      return fallback;
    }

    const path = `${parsed.pathname}${parsed.search}${parsed.hash}`;

    // Normalisation can collapse `/..//host` into `//host`, which a browser
    // would read as protocol-relative when the string is used on its own.
    if (!path.startsWith("/") || path.startsWith("//")) {
      return fallback;
    }

    return path;
  } catch {
    return fallback;
  }
}
