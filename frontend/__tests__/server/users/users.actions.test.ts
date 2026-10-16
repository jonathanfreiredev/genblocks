// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { server } from "../../msw/server";

vi.mock("@/server/auth/auth.lib", () => ({
  getSession: vi.fn(),
}));

vi.mock("@/lib/supabase/server", () => ({
  createClient: vi.fn(),
}));

vi.mock("@/lib/supabase/admin", () => ({
  createAdminClient: vi.fn(),
}));

import { getSession } from "@/server/auth/auth.lib";
import { createAdminClient } from "@/lib/supabase/admin";
import { createClient } from "@/lib/supabase/server";
import {
  deleteUserAction,
  updateUserAction,
} from "@/server/users/users.actions";

const BACKEND_URL = "http://backend.test";
const USER_EMAIL = "user@example.com";
const USER_ID = "user-id";

const signInWithPassword = vi.fn();
const signOut = vi.fn();
const adminDeleteUser = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();

  // `protectedProcedure` resolves the session through `getSession`.
  vi.mocked(getSession).mockResolvedValue({
    session: { token: "token", expiresAt: null },
    user: { id: USER_ID, email: USER_EMAIL, name: "User", isVerified: true },
  });

  signInWithPassword.mockResolvedValue({ error: null });
  signOut.mockResolvedValue({ error: null });
  adminDeleteUser.mockResolvedValue({ error: null });

  // The update action only touches `auth.getUser` when the email is unchanged.
  vi.mocked(createClient).mockResolvedValue({
    auth: {
      getUser: vi.fn().mockResolvedValue({
        data: { user: { email: USER_EMAIL } },
      }),
      signInWithPassword,
      signOut,
    },
  } as unknown as Awaited<ReturnType<typeof createClient>>);

  vi.mocked(createAdminClient).mockReturnValue({
    auth: { admin: { deleteUser: adminDeleteUser } },
  } as unknown as ReturnType<typeof createAdminClient>);
});

describe("updateUserAction", () => {
  test("returns the profile updated by the backend", async () => {
    server.use(
      http.patch(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json({ full_name: "New Name" }),
      ),
    );

    const result = await updateUserAction({
      name: "New Name",
      email: USER_EMAIL,
    });

    expect(result.serverError).toBeUndefined();
    expect(result.data).toEqual({
      success: true,
      user: { full_name: "New Name" },
    });
  });

  test("surfaces a string backend error message", async () => {
    server.use(
      http.patch(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json({ detail: "Not allowed" }, { status: 403 }),
      ),
    );

    const result = await updateUserAction({
      name: "New Name",
      email: USER_EMAIL,
    });

    expect(result.serverError?.code).toBe(403);
    expect(result.serverError?.message).toBe("Not allowed");
  });

  test("normalises a FastAPI validation error list into a string message", async () => {
    server.use(
      http.patch(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json(
          {
            detail: [
              {
                loc: ["body", "full_name"],
                msg: "String should have at least 2 characters",
                type: "string_too_short",
              },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    const result = await updateUserAction({
      name: "New Name",
      email: USER_EMAIL,
    });

    expect(result.serverError?.code).toBe(422);
    expect(result.serverError?.message).toBe(
      "String should have at least 2 characters",
    );
  });
});

describe("deleteUserAction", () => {
  test("deletes the profile and the Supabase user, then signs out", async () => {
    server.use(
      http.delete(
        `${BACKEND_URL}/v1/users/me`,
        () => new HttpResponse(null, { status: 204 }),
      ),
    );

    const result = await deleteUserAction({ password: "secret" });

    expect(result.serverError).toBeUndefined();
    expect(result.data).toEqual({ success: true });
    expect(adminDeleteUser).toHaveBeenCalledWith(USER_ID);
    expect(signOut).toHaveBeenCalled();
  });

  test("rejects a wrong password without touching the backend", async () => {
    signInWithPassword.mockResolvedValue({ error: { message: "bad" } });

    const result = await deleteUserAction({ password: "wrong" });

    expect(result.serverError?.message).toBe("Incorrect password.");
    expect(adminDeleteUser).not.toHaveBeenCalled();
  });

  test("surfaces a backend error and keeps the account", async () => {
    server.use(
      http.delete(`${BACKEND_URL}/v1/users/me`, () =>
        HttpResponse.json({ detail: "Nope" }, { status: 500 }),
      ),
    );

    const result = await deleteUserAction({ password: "secret" });

    expect(result.serverError?.code).toBe(500);
    expect(result.serverError?.message).toBe("Nope");
    expect(adminDeleteUser).not.toHaveBeenCalled();
    expect(signOut).not.toHaveBeenCalled();
  });
});
