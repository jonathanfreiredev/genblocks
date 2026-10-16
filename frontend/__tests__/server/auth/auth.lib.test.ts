// @vitest-environment node
import { http, HttpResponse } from "msw";
import { describe, expect, test, vi } from "vitest";

import { server } from "../../msw/server";

vi.mock("@/lib/supabase/server", () => ({
  createClient: vi.fn(),
}));

import { createClient } from "@/lib/supabase/server";
import { getSession } from "@/server/auth/auth.lib";

const BACKEND_URL = "http://backend.test";

function mockSupabase(
  options: {
    claims?: Record<string, unknown>;
    claimsError?: unknown;
    session?: { access_token: string; expires_at: number } | null;
  } = {},
) {
  const { claims, claimsError = null, session = null } = options;

  vi.mocked(createClient).mockResolvedValue({
    auth: {
      getClaims: vi.fn().mockResolvedValue({
        data: claims ? { claims } : null,
        error: claimsError,
      }),
      getSession: vi.fn().mockResolvedValue({ data: { session } }),
    },
  } as unknown as Awaited<ReturnType<typeof createClient>>);
}

describe("getSession", () => {
  test("returns null when the claims cannot be verified", async () => {
    mockSupabase({ claimsError: new Error("invalid token") });

    await expect(getSession()).resolves.toBeNull();
  });

  test("maps the claims and the backend profile into a session", async () => {
    mockSupabase({
      claims: {
        sub: "user-id",
        email: "user@example.com",
        user_metadata: { full_name: "From metadata", email_verified: true },
      },
      session: { access_token: "token", expires_at: 1_700_000_000 },
    });
    server.use(
      http.get(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json({ full_name: "From backend" }),
      ),
    );

    await expect(getSession()).resolves.toEqual({
      session: {
        token: "token",
        expiresAt: new Date(1_700_000_000 * 1000).toISOString(),
      },
      user: {
        id: "user-id",
        email: "user@example.com",
        name: "From backend",
        isVerified: true,
      },
    });
  });

  test("falls back to the metadata name when the backend fails", async () => {
    mockSupabase({
      claims: {
        sub: "user-id",
        email: "user@example.com",
        user_metadata: { full_name: "From metadata" },
      },
      session: { access_token: "token", expires_at: 1_700_000_000 },
    });
    server.use(
      http.get(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json({ detail: "boom" }, { status: 500 }),
      ),
    );

    const session = await getSession();

    expect(session?.user.name).toBe("From metadata");
  });

  test("marks the user unverified when email_verified is false", async () => {
    mockSupabase({
      claims: {
        sub: "user-id",
        email: "user@example.com",
        user_metadata: { email_verified: false },
      },
      session: { access_token: "token", expires_at: 1_700_000_000 },
    });
    server.use(
      http.get(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json({ full_name: "Name" }),
      ),
    );

    const session = await getSession();

    expect(session?.user.isVerified).toBe(false);
  });
});
