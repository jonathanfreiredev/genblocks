/**
 * Resolve a `next` search parameter to a path on this origin.
 *
 * A `next` value arrives in a URL, so it is attacker-controlled: redirecting to
 * it unchecked turns any page that honours it into an open redirect. Only
 * same-origin paths are accepted, and anything else falls back.
 */
export function safeNextPath(
  value: string | null | undefined,
  fallback = "/",
): string {
  // Off-origin already: an absolute URL, a protocol-relative "//host" path, or
  // something that does not start with a slash at all (which, concatenated onto
  // an origin, becomes "https://oursite.com@evil.com").
  if (!value || !value.startsWith("/") || value.startsWith("//")) {
    return fallback;
  }

  // Browsers and URL parsers normalise these inconsistently: "/\evil.com"
  // becomes "//evil.com" in some of them.
  if (/[\s\\]/.test(value)) {
    return fallback;
  }

  return value;
}
