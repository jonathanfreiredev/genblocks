/**
 * Browser-side fences for every page this app serves.
 *
 * The preview route is deliberately not covered here: it hosts generated code
 * and carries its own policy (see `lib/vault/preview.ts`), including a
 * `frame-ancestors 'self'` that lets the item view embed it.
 */
export function securityHeaders(
  production = process.env.NODE_ENV === "production",
): Record<string, string> {
  const script = production
    ? "'self' 'unsafe-inline'"
    : "'self' 'unsafe-inline' 'unsafe-eval'";
  const connect = production ? "'self'" : "'self' ws: wss:";

  const csp = [
    "default-src 'self'",
    `script-src ${script}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https://res.cloudinary.com",
    "font-src 'self' data:",
    `connect-src ${connect}`,
    "frame-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    "manifest-src 'self'",
    "media-src 'self'",
    "worker-src 'self' blob:",
    ...(production ? ["upgrade-insecure-requests"] : []),
  ].join("; ");

  return {
    "Content-Security-Policy": csp,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy":
      "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    ...(production
      ? { "Strict-Transport-Security": "max-age=31536000; includeSubDomains" }
      : {}),
  };
}
