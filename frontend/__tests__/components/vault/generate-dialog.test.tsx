import { fireEvent, render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { server } from "../../msw/server";

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

import { GenerateDialog } from "@/components/vault/generate-dialog";
import type { Task, TaskDetail } from "@/lib/vault/types";

const MESSAGE = "A pricing page for a developer tool.";
const TASK_ID = "0b9c1e2a-1111-2222-3333-444455556666";
const COMPONENT_ID = "7c1d2e3f-4444-5555-6666-777788889999";

/** The row the queue hands back: queued, and with no checklist yet. */
const QUEUED: Task = {
  id: TASK_ID,
  kind: "generate_component",
  status: "pending",
  brief: MESSAGE,
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

/** A turn as the backend streams it. */
function turn(...events: Array<[string, unknown]>) {
  const stream = events
    .map(([name, data]) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`)
    .join("");

  return new HttpResponse(stream, {
    headers: { "Content-Type": "text/event-stream" },
  });
}

/** Opens the dialog. */
async function open() {
  render(<GenerateDialog />);
  fireEvent.click(screen.getByRole("button", { name: "Generate with AI" }));
  await screen.findByText(/What should I build/);
}

/** Opens the dialog and says one thing to the agent. */
async function send(message: string = MESSAGE) {
  await open();
  fireEvent.change(screen.getByLabelText("Message"), {
    target: { value: message },
  });
  fireEvent.click(screen.getByRole("button", { name: "Send" }));
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("GenerateDialog", () => {
  test("sends what was said and streams the answer back", async () => {
    let sent: unknown = null;

    server.use(
      http.post("/api/agent/chat", async ({ request }) => {
        sent = await request.json();

        return turn(
          ["tool", { name: "search_components", state: "started" }],
          ["tool", { name: "search_components", state: "finished" }],
          ["token", { text: "Nothing close" }],
          ["token", { text: " is in the registry." }],
          ["done", {}],
        );
      }),
    );

    await send();

    // The words arrive as pieces and are read as one answer.
    expect(
      await screen.findByText(/Nothing close is in the registry./),
    ).toBeInTheDocument();
    // What was said sits in the conversation, and the composer is empty again.
    expect(screen.getByText(MESSAGE)).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toHaveValue("");

    // The tool the agent reached for is named, and the conversation is named so
    // the next turn can carry on from it.
    expect(screen.getByRole("status")).toHaveTextContent(
      "Searched the registry",
    );
    expect(sent).toEqual({
      message: MESSAGE,
      threadId: expect.any(String),
    });
  });

  test("queues the task the agent made and follows it", async () => {
    server.use(
      http.post("/api/agent/chat", () =>
        turn(
          ["tool", { name: "create_component", state: "started" }],
          ["tool", { name: "create_component", state: "finished" }],
          ["task", QUEUED],
          ["token", { text: "Queued it. Follow the checklist below." }],
          ["done", {}],
        ),
      ),
      http.get("/api/tasks/:id", () => HttpResponse.json(FINISHED)),
    );

    await send();

    // The row exists but no worker has opened it: the dialog says that rather
    // than drawing an empty checklist.
    expect(
      await screen.findByText(/No worker has opened this task yet/),
    ).toBeInTheDocument();

    // Then the poll reads the same task, finished, and the checklist and the way
    // to the block arrive without another click.
    expect(
      await screen.findByText("Succeeded", {}, { timeout: 2500 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Publishing the block")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open the block" }),
    ).toHaveAttribute("href", `/?kind=component&item=${COMPONENT_ID}`);

    // The page behind the dialog was told, so it does not sit on "Running".
    expect(refresh).toHaveBeenCalled();

    // The conversation is over: the task is the record now, and there is nothing
    // left to say to the agent.
    expect(screen.queryByLabelText("Message")).toBeNull();
    expect(
      screen.getByText(/The conversation ends where the task starts/),
    ).toBeInTheDocument();
  });

  test("says so when the agent cannot be reached", async () => {
    server.use(
      http.post("/api/agent/chat", () =>
        HttpResponse.json(
          { error: "The agent did not answer. Nothing was queued." },
          { status: 502 },
        ),
      ),
    );

    await send();

    expect(
      await screen.findByText("The turn did not finish"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("The agent did not answer. Nothing was queued."),
    ).toBeInTheDocument();
    // The answer that never came left no empty bubble, and the composer is still
    // there to try again.
    expect(screen.queryByLabelText("The agent is answering")).toBeNull();
    expect(screen.getByLabelText("Message")).toBeInTheDocument();
  });

  test("keeps what was said when a turn dies mid-answer", async () => {
    server.use(
      http.post("/api/agent/chat", () =>
        turn(
          ["token", { text: "Let me look at " }],
          ["token", { text: "the registry." }],
          [
            "error",
            { message: "The agent stopped mid-answer. Nothing was queued." },
          ],
          ["done", {}],
        ),
      ),
    );

    await send();

    // Half an answer is worth keeping: it is what the agent managed to say.
    expect(
      await screen.findByText(/Let me look at the registry./),
    ).toBeInTheDocument();
    expect(
      screen.getByText("The agent stopped mid-answer. Nothing was queued."),
    ).toBeInTheDocument();
  });

  test("sends on Enter and keeps Shift+Enter for a new line", async () => {
    const post = vi.fn();

    server.use(
      http.post("/api/agent/chat", () => {
        post();
        return turn(["token", { text: "Looking." }], ["done", {}]);
      }),
    );

    await open();
    const box = screen.getByLabelText("Message");
    fireEvent.change(box, { target: { value: MESSAGE } });

    fireEvent.keyDown(box, { key: "Enter", shiftKey: true });
    expect(post).not.toHaveBeenCalled();

    fireEvent.keyDown(box, { key: "Enter" });
    expect(await screen.findByText("Looking.")).toBeInTheDocument();
    expect(post).toHaveBeenCalled();
  });

  test("sends a visitor to sign in rather than taking a message", async () => {
    render(<GenerateDialog signedIn={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Generate with AI" }));

    expect(
      await screen.findByText(/Queueing a block needs an account/),
    ).toBeInTheDocument();

    expect(screen.queryByLabelText("Message")).toBeNull();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/auth/login?next=%2F",
    );
  });

  test("will not send nothing, or more than a message can hold", async () => {
    await open();
    const box = screen.getByLabelText("Message");

    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();

    fireEvent.change(box, { target: { value: MESSAGE } });
    expect(screen.getByRole("button", { name: "Send" })).toBeEnabled();

    fireEvent.change(box, { target: { value: "a".repeat(4001) } });
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });
});
