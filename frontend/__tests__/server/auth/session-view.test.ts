import { describe, expect, test } from "vitest";

import type { Session } from "@/server/auth/auth.lib";
import { sessionView } from "@/server/auth/session-view";

const SESSION: Session = {
  session: {
    token: "a-real-access-token",
    expiresAt: "2026-10-21T12:00:00Z",
  },
  user: {
    id: "0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
    email: "marisol@example.com",
    name: "Marisol Vega",
    isVerified: true,
    isAdmin: false,
    hasPassword: true,
  },
};

describe("sessionView", () => {
  test("keeps the name and drops the access token", () => {
    const view = sessionView(SESSION);

    expect(view).toEqual({ user: { name: "Marisol Vega" } });
    expect(JSON.stringify(view)).not.toContain(SESSION.session.token);
    expect(view).not.toHaveProperty("session");
  });

  test("is null for an anonymous visitor", () => {
    expect(sessionView(null)).toBeNull();
  });
});
