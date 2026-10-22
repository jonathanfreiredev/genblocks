/**
 * Surfaces that belong to an account or an operator, never to the index.
 *
 * The same list feeds `robots.ts` and the response header in the proxy. The
 * header matters because a crawler that already has the URL can still fetch it
 * before it reads the page: `noindex` is stronger than a `Disallow`.
 */
const PRIVATE_PREFIXES = [
  "/api",
  "/auth",
  "/oauth",
  "/tasks",
  "/profile",
  "/admin",
] as const;

export function isPrivatePath(pathname: string): boolean {
  return PRIVATE_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export const PRIVATE_ROBOTS_PATHS = [...PRIVATE_PREFIXES];
