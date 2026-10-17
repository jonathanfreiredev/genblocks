// @vitest-environment node
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { server } from "../../msw/server";

vi.mock("@/server/auth/auth.lib", () => ({
  getSession: vi.fn(),
}));

import { getSession } from "@/server/auth/auth.lib";
import { createTaskAction } from "@/server/tasks/tasks.actions";
import type { Task } from "@/lib/vault/types";

const BACKEND_URL = "http://backend.test";
const BRIEF = "A pricing page for a developer tool: three tiers and a toggle.";

const TASK: Task = {
  id: "0b9c1e2a-1111-2222-3333-444455556666",
  kind: "component",
  status: "pending",
  brief: BRIEF,
  component_id: null,
  created_at: "2026-10-17T09:12:00Z",
  finished_at: null,
  error: null,
  langfuse_trace_id: null,
  steps: [],
};

beforeEach(() => {
  vi.clearAllMocks();

  // `protectedProcedure` resolves the session through `getSession`.
  vi.mocked(getSession).mockResolvedValue({
    session: { token: "token", expiresAt: null },
    user: {
      id: "user-id",
      email: "user@example.com",
      name: "User",
      isVerified: true,
    },
  });
});

describe("createTaskAction", () => {
  test("queues the brief with the caller's own token", async () => {
    server.use(
      http.post(`${BACKEND_URL}/v1/tasks`, async ({ request }) => {
        expect(request.headers.get("Authorization")).toBe("Bearer token");
        // The brief is trimmed on this side too, so the row never holds the
        // padding the browser happened to send.
        expect(await request.json()).toEqual({ brief: BRIEF });
        return HttpResponse.json(TASK, { status: 202 });
      }),
    );

    const result = await createTaskAction({ brief: `  ${BRIEF}  ` });

    expect(result?.serverError).toBeUndefined();
    expect(result?.data?.task).toEqual(TASK);
  });

  test("surfaces a string backend error message", async () => {
    server.use(
      http.post(`${BACKEND_URL}/v1/tasks`, () =>
        HttpResponse.json({ detail: "Not allowed" }, { status: 403 }),
      ),
    );

    const result = await createTaskAction({ brief: BRIEF });

    expect(result?.serverError?.code).toBe(403);
    expect(result?.serverError?.message).toBe("Not allowed");
  });

  test("normalises a FastAPI validation error list into a string message", async () => {
    server.use(
      http.post(`${BACKEND_URL}/v1/tasks`, () =>
        HttpResponse.json(
          {
            detail: [
              {
                loc: ["body", "brief"],
                msg: "String should have at least 10 characters",
                type: "string_too_short",
              },
            ],
          },
          { status: 422 },
        ),
      ),
    );

    const result = await createTaskAction({ brief: BRIEF });

    expect(result?.serverError?.code).toBe(422);
    expect(result?.serverError?.message).toBe(
      "String should have at least 10 characters",
    );
  });

  test("refuses a brief too short to be one, without calling the backend", async () => {
    const post = vi.fn();
    server.use(
      http.post(`${BACKEND_URL}/v1/tasks`, () => {
        post();
        return HttpResponse.json(TASK, { status: 202 });
      }),
    );

    const result = await createTaskAction({ brief: "a page" });

    expect(result?.validationErrors?.brief).toBeDefined();
    expect(result?.data).toBeUndefined();
    expect(post).not.toHaveBeenCalled();
  });
});
