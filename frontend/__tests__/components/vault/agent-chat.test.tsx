import { fireEvent, render, screen } from "@testing-library/react";
import { HttpResponse, http } from "msw";
import { beforeEach, describe, expect, test, vi } from "vitest";

import { server } from "../../msw/server";

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

import { AgentChat } from "@/components/vault/agent-chat";
import type { Task, TaskDetail } from "@/lib/vault/types";

const MESSAGE = "A pricing page for a developer tool.";
const TASK_ID = "0b9c1e2a-1111-2222-3333-444455556666";
const COMPONENT_ID = "7c1d2e3f-4444-5555-6666-777788889999";
const THREAD_KEY = "genblocks-chat-thread";

/** The row the queue hands back: queued, and with no checklist yet. */
const QUEUED: Task = {
  id: TASK_ID,
  kind: "generate_component",
  status: "pending",
  brief: MESSAGE,
  component_id: null,
  image_id: null,
  image_width: null,
  image_height: null,
  image_category_id: null,
  created_at: "2026-10-17T09:12:00Z",
  finished_at: null,
  error: null,
  langfuse_trace_id: null,
  cached: false,
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
  render(<AgentChat userName="Marisol Vega" />);
  fireEvent.click(screen.getByRole("button", { name: "Ask AI" }));
  await screen.findByText(/Ask about anything in the vault/);
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
  window.localStorage.clear();
});

describe("AgentChat", () => {
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

    // The tool the agent reached for is named as a finished step.
    expect(screen.getByText("Searched the blocks")).toBeInTheDocument();
    expect(sent).toEqual({
      message: MESSAGE,
      threadId: expect.any(String),
    });

    // The id is the only thing kept between visits.
    expect(window.localStorage.getItem(THREAD_KEY)).toBe(
      (sent as { threadId: string }).threadId,
    );
  });

  test("queues the task the agent made and keeps the conversation open", async () => {
    server.use(
      http.post("/api/agent/chat", () =>
        turn(
          ["tool", { name: "create_component", state: "started" }],
          ["tool", { name: "create_component", state: "finished" }],
          ["task", QUEUED],
          ["token", { text: "Queued it. The task card is the record." }],
          ["done", {}],
        ),
      ),
      http.get("/api/tasks/:id", () => HttpResponse.json(FINISHED)),
    );

    await send();

    // The row exists but no worker has opened it: the card says that rather than
    // drawing an empty checklist.
    expect(
      await screen.findByText(/Waiting for a worker to open it/),
    ).toBeInTheDocument();

    // Then the poll reads the same task, finished, and the steps and the way to
    // the block arrive without another click.
    expect(
      await screen.findByText("Succeeded", {}, { timeout: 2500 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Publishing the block")).toBeInTheDocument();
    expect(screen.getByText("Block published")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open the block" }),
    ).toHaveAttribute("href", `/blocks/${COMPONENT_ID}`);

    // The page behind the dialog was told, so it does not sit on "Running".
    expect(refresh).toHaveBeenCalled();

    // The chat is not over: the task has its card, and the person can keep
    // asking questions.
    expect(screen.getByLabelText("Message")).toBeInTheDocument();
  });

  test("prepares a brief and queues only when the person confirms", async () => {
    let confirmed: unknown = null;

    server.use(
      http.post("/api/agent/chat", () =>
        turn(
          ["proposal", { brief: MESSAGE, force: false }],
          ["token", { text: "The brief is ready." }],
          ["done", {}],
        ),
      ),
      http.post("/api/agent/confirm", async ({ request }) => {
        confirmed = await request.json();
        return HttpResponse.json(QUEUED, { status: 202 });
      }),
      http.get("/api/tasks/:id", () => HttpResponse.json(QUEUED)),
    );

    await send();

    // The agent prepared the brief; nothing was queued by the model.
    expect(await screen.findByText("Ready to build")).toBeInTheDocument();
    expect(screen.getAllByText(MESSAGE).length).toBeGreaterThan(0);
    expect(screen.queryByText(/Waiting for a worker/)).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Queue block" }));

    expect(
      await screen.findByText(/Waiting for a worker to open it/),
    ).toBeInTheDocument();
    expect(confirmed).toEqual({
      kind: "component",
      brief: MESSAGE,
      force: false,
      width: null,
      height: null,
      category: null,
    });
    expect(screen.queryByText("Ready to build")).toBeNull();
  });

  test("says the registry already had the block instead of pretending it built one", async () => {
    const cached: Task = {
      ...QUEUED,
      status: "succeeded",
      component_id: COMPONENT_ID,
      finished_at: "2026-10-17T09:12:02Z",
      cached: true,
      steps: [
        {
          id: "step-0",
          index: 0,
          name: "Found in the registry",
          status: "succeeded",
          detail: null,
          started_at: "2026-10-17T09:12:02Z",
          finished_at: "2026-10-17T09:12:02Z",
        },
      ],
    };

    server.use(
      http.post("/api/agent/chat", () =>
        turn(
          ["task", cached],
          ["token", { text: "That one already exists." }],
          ["done", {}],
        ),
      ),
    );

    await send();

    // The task is finished on arrival, so the card says what happened: a lookup,
    // not a build.
    expect(
      await screen.findByText("Already in the registry"),
    ).toBeInTheDocument();
    expect(screen.getByText("Found in the registry")).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open the block" }),
    ).toHaveAttribute("href", `/blocks/${COMPONENT_ID}`);
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
      await screen.findByText("The agent did not answer. Nothing was queued."),
    ).toBeInTheDocument();
    // The answer that never came left no empty bubble, and the composer is still
    // there to try again.
    expect(screen.queryByText("Thinking…")).toBeNull();
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

  test("starts a new conversation and rotates the stored id", async () => {
    server.use(
      http.post("/api/agent/chat", () =>
        turn(["token", { text: "First answer." }], ["done", {}]),
      ),
    );

    await send();
    await screen.findByText("First answer.");

    const before = window.localStorage.getItem(THREAD_KEY);
    expect(before).toEqual(expect.any(String));

    fireEvent.click(
      screen.getByRole("button", { name: "Start a new conversation" }),
    );

    // The transcript is gone, and the next send belongs to a different thread.
    await screen.findByText(/Ask about anything in the vault/);
    expect(window.localStorage.getItem(THREAD_KEY)).not.toBe(before);
  });

  test("sends a visitor to sign in rather than taking a message", async () => {
    render(<AgentChat signedIn={false} />);

    fireEvent.click(screen.getByRole("button", { name: "Ask AI" }));

    expect(await screen.findByText(/needs an account/)).toBeInTheDocument();

    expect(screen.queryByLabelText("Message")).toBeNull();
    expect(screen.getByRole("link", { name: "Sign in" })).toHaveAttribute(
      "href",
      "/auth/login?next=%2Fblocks",
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
