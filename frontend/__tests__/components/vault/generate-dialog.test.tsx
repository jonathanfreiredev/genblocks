import { fireEvent, render, screen } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { server } from "../../msw/server";

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/server/tasks/tasks.actions", () => ({
  createTaskAction: vi.fn(),
}));

import { GenerateDialog } from "@/components/vault/generate-dialog";
import { createTaskAction } from "@/server/tasks/tasks.actions";
import type { Task, TaskDetail } from "@/lib/vault/types";

const BRIEF = "A pricing page for a developer tool: three tiers and a toggle.";
const TASK_ID = "0b9c1e2a-1111-2222-3333-444455556666";
const COMPONENT_ID = "7c1d2e3f-4444-5555-6666-777788889999";

/** The row the queue hands back: queued, and with no checklist yet. */
const QUEUED: Task = {
  id: TASK_ID,
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

/** The same task a moment later, as the worker left it. */
const FINISHED: TaskDetail = {
  ...QUEUED,
  status: "succeeded",
  component_id: COMPONENT_ID,
  finished_at: "2026-10-17T09:12:02Z",
  steps: [
    "Retrieving references",
    "Generating the block",
    "Judging the attempt",
    "Publishing the block",
  ].map((name, index) => ({
    id: `step-${index}`,
    index,
    name,
    status: "succeeded" as const,
    detail: null,
    started_at: "2026-10-17T09:12:00Z",
    finished_at: "2026-10-17T09:12:01Z",
  })),
  generations: [],
};

/** Opens the dialog and answers with a brief. */
async function answer(brief: string) {
  render(<GenerateDialog />);

  fireEvent.click(screen.getByRole("button", { name: "Generate with AI" }));
  await screen.findByText(/What should I build/);

  fireEvent.change(screen.getByLabelText("Brief"), {
    target: { value: brief },
  });
  fireEvent.click(screen.getByRole("button", { name: "Answer" }));
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("GenerateDialog", () => {
  test("reads the brief back before it becomes a task", async () => {
    await answer(BRIEF);

    expect(
      await screen.findByText(/I will queue this brief as one task/),
    ).toBeInTheDocument();

    // The visitor's own words, once: as the turn they took.
    expect(screen.getByText(BRIEF)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Edit the brief" }),
    ).toBeInTheDocument();
  });

  test("queues the trimmed brief and follows the task it makes", async () => {
    vi.mocked(createTaskAction).mockResolvedValue({ data: { task: QUEUED } });

    server.use(http.get("/api/tasks/:id", () => HttpResponse.json(FINISHED)));

    await answer(`  ${BRIEF}  `);

    fireEvent.click(
      await screen.findByRole("button", { name: "Queue the task" }),
    );

    expect(createTaskAction).toHaveBeenCalledWith({ brief: BRIEF });

    // The row exists but no worker has opened it: the dialog says that rather
    // than drawing an empty checklist.
    expect(
      await screen.findByText(/No worker has opened this task yet/),
    ).toBeInTheDocument();

    // Then the poll reads the same task, finished, and the checklist and the
    // way to the block arrive without another click.
    expect(
      await screen.findByText("Succeeded", {}, { timeout: 2500 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Publishing the block")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open the block" }),
    ).toHaveAttribute("href", `/?kind=component&item=${COMPONENT_ID}`);

    // The page behind the dialog was told, so it does not sit on "Running".
    expect(refresh).toHaveBeenCalled();
  });

  test("sends a visitor to sign in rather than taking a brief", async () => {
    render(<GenerateDialog signedIn={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Generate with AI" }));

    expect(
      await screen.findByText(/Queueing a block needs an account/),
    ).toBeInTheDocument();

    expect(screen.queryByLabelText("Brief")).toBeNull();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/auth/login?next=%2F",
    );
  });

  test("will not answer with a brief too short to be one", async () => {
    render(<GenerateDialog />);

    fireEvent.click(screen.getByRole("button", { name: "Generate with AI" }));
    await screen.findByText(/What should I build/);

    const field = screen.getByLabelText("Brief");

    expect(screen.getByRole("button", { name: "Answer" })).toBeDisabled();

    fireEvent.change(field, { target: { value: BRIEF } });

    expect(screen.getByRole("button", { name: "Answer" })).toBeEnabled();
  });

  test("says so when the queue refuses the brief", async () => {
    vi.mocked(createTaskAction).mockResolvedValue({
      serverError: { code: 403, message: "Not allowed" },
    });

    await answer(BRIEF);

    fireEvent.click(
      await screen.findByRole("button", { name: "Queue the task" }),
    );

    expect(
      await screen.findByText("The brief did not reach the queue"),
    ).toBeInTheDocument();
    expect(screen.getByText("Not allowed")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Follow the task" })).toBeNull();
  });
});
