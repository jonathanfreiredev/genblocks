import { describe, expect, test, vi } from "vitest";

import { cookieOptions } from "@/lib/supabase/cookie-options";

describe("cookieOptions", () => {
  test("applies server-only, non-production defaults", () => {
    expect(cookieOptions).toEqual({
      path: "/",
      sameSite: "lax",
      httpOnly: true,
      secure: false,
    });
  });

  test("marks the cookies secure in production", async () => {
    // The option is computed at import time, so re-import under a stubbed env.
    vi.stubEnv("NODE_ENV", "production");
    vi.resetModules();

    const { cookieOptions: productionCookieOptions } =
      await import("@/lib/supabase/cookie-options");

    expect(productionCookieOptions.secure).toBe(true);
  });
});
