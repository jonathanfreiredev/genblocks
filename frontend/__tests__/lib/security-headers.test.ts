import { describe, expect, test } from "vitest";

import { securityHeaders } from "@/lib/security-headers";

describe("securityHeaders", () => {
  test("keeps the app out of frames and sends the usual companions", () => {
    const headers = securityHeaders(true);

    expect(headers["X-Frame-Options"]).toBe("DENY");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("strict-origin-when-cross-origin");
    expect(headers["Content-Security-Policy"]).toContain(
      "frame-ancestors 'none'",
    );
    expect(headers["Content-Security-Policy"]).toContain("frame-src 'self'");
  });

  test("only pins HTTPS in production", () => {
    expect(securityHeaders(true)["Strict-Transport-Security"]).toContain(
      "max-age=",
    );
    expect(securityHeaders(false)["Strict-Transport-Security"]).toBeUndefined();
  });

  test("allows the development bundler to evaluate, but not production", () => {
    expect(securityHeaders(false)["Content-Security-Policy"]).toContain(
      "'unsafe-eval'",
    );
    expect(securityHeaders(true)["Content-Security-Policy"]).not.toContain(
      "'unsafe-eval'",
    );
  });
});
