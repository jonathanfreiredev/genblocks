"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
  type ReactNode,
} from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldLabel } from "@/components/ui/field";
import { Message, MessageContent, MessageGroup } from "@/components/ui/message";
import { Textarea } from "@/components/ui/textarea";
import { StatusWord } from "@/components/vault/status-word";
import { TaskChecklist } from "@/components/vault/task-checklist";
import { readTurn } from "@/lib/agent/stream";
import type { AgentEvent } from "@/lib/agent/events";
import { cn } from "@/lib/utils";
import { TASK_STATUS_LABELS } from "@/lib/vault/task-status";
import type { Task, TaskDetail, TaskStatus } from "@/lib/vault/types";
import { MESSAGE_MAX_LENGTH } from "@/server/agent/agent.schemas";

/**
 * How often the dialog re-reads the task while a worker is on it.
 *
 * The checklist is a record of one row, so this is a cheap read; a second is
 * short enough that the steps appear to fill in, and long enough that a dialog
 * left open on a finished task is not a poll at all — the loop stops.
 */
const POLL_MS = 1000;

const LIVE_STATUSES: TaskStatus[] = ["pending", "running"];

function isLive(status: TaskStatus): boolean {
  return LIVE_STATUSES.includes(status);
}

/**
 * The surface's own opening line.
 *
 * The greeting belongs to the page, not to the model. The agent answers from the
 * first thing the person says, and a template dressed up as its words would be
 * the small lie this phase exists to end.
 */
const GREETING =
  "What should I build? The block, what it is for, and anything it must avoid. I will ask for whatever is missing.";

const VISITOR =
  "Queueing a block needs an account: the task belongs to whoever asks for it. Sign in and the brief is yours.";

/**
 * What the generator says once the brief is its problem.
 *
 * These describe the task, not the agent: from the moment it exists, the
 * checklist is the record.
 */
const QUEUED_LINES: Record<TaskStatus, string> = {
  pending:
    "Queued. The checklist below is the task's own record, and it fills in once a worker claims it.",
  running: "Running. Each step closes as the worker finishes it.",
  succeeded: "Published, and scored. The block is in the vault.",
  failed: "The task stopped. What it said is below.",
  interrupted:
    "The worker went away mid-run, so this one is unfinished. The record is kept.",
};

/** How a tool call reads while it runs, and once it is over. */
const TOOL_LINES: Record<string, { running: string; done: string }> = {
  search_components: {
    running: "Searching the registry",
    done: "Searched the registry",
  },
  create_component: { running: "Queueing the task", done: "Queued the task" },
};

const UNKNOWN_TOOL = { running: "Calling a tool", done: "Called a tool" };

/** A stable name for the by-then-empty bubble the browser wrote a task into. */
const NO_ANSWER = "Nothing was queued.";

interface Turn {
  id: number;
  from: "you" | "agent";
  text: string;
}

interface Activity {
  name: string;
  state: "started" | "finished";
}

/**
 * One turn in the conversation.
 *
 * The generator speaks on the canvas — a bubble with no surface of its own —
 * and the visitor's words sit in a stone well, quoted the way this system
 * quotes anything it did not write. The label names the speaker in mono so the
 * exchange survives being read aloud.
 */
function Turn({
  from,
  align = "start",
  children,
}: {
  from: string;
  align?: "start" | "end";
  children: ReactNode;
}) {
  return (
    <Message align={align}>
      <MessageContent>
        <span className="type-label text-ink-faint">{from}</span>
        <Bubble variant={align === "end" ? "muted" : "ghost"} align={align}>
          <BubbleContent className="whitespace-pre-wrap">
            {children}
          </BubbleContent>
        </Bubble>
      </MessageContent>
    </Message>
  );
}

/** Add one token to the answer it belongs to. */
function appendTo(turns: Turn[], id: number, text: string): Turn[] {
  return turns.map((turn) =>
    turn.id === id ? { ...turn, text: turn.text + text } : turn,
  );
}

/** Drop an answer that never said anything, so a failure leaves no empty bubble. */
function dropIfUnsaid(turns: Turn[], id: number): Turn[] {
  return turns.filter((turn) => turn.id !== id || turn.text !== "");
}

/** What the route handler said when the agent could not be reached. */
async function unreadable(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);
  const said =
    body && typeof body === "object" && "error" in body
      ? (body as { error: unknown }).error
      : null;

  return typeof said === "string" ? said : NO_ANSWER;
}

/**
 * The vault's one action: a conversation, and the task it becomes.
 *
 * The conversation is the surface (PLAN.md, decision 5) and it ends where the
 * generation starts — this is not a chat about the collection. The agent is
 * real: it reads the brief, searches the registry for anything close, and queues
 * one task. The pipeline behind the task is still canned, which the checklist
 * says for itself rather than hiding.
 *
 * `signedIn` is false on the public gallery, where the vault can be read but
 * nothing can be asked for: the account is what a task hangs off, so a visitor
 * is sent to sign in rather than allowed to start a conversation the guard would
 * refuse on the way out.
 */
export function GenerateDialog({
  signedIn = true,
  className,
}: {
  signedIn?: boolean;
  className?: string;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [activity, setActivity] = useState<Activity | null>(null);
  const [thinking, setThinking] = useState(false);
  const [task, setTask] = useState<Task | null>(null);
  const [trouble, setTrouble] = useState<string | null>(null);
  const [following, setFollowing] = useState(true);

  // The conversation the turns belong to. Named here and kept for as long as the
  // dialog is open, because the memory on the other end is one per thread.
  const conversation = useRef<string | null>(null);
  const counter = useRef(0);
  const inFlight = useRef<AbortController | null>(null);
  const viewport = useRef<HTMLDivElement | null>(null);

  const written = draft.trim();
  const ready = written.length > 0 && written.length <= MESSAGE_MAX_LENGTH;

  const taskId = task?.id ?? null;
  const live = task !== null && isLive(task.status);

  useEffect(() => {
    if (!open || taskId === null || !live) {
      return;
    }

    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;

    const read = async () => {
      try {
        const response = await fetch(`/api/tasks/${taskId}`, {
          cache: "no-store",
        });

        if (response.ok) {
          const next = (await response.json()) as TaskDetail;
          setTask(next);

          if (!isLive(next.status)) {
            // The page behind the dialog is a server render of this same task.
            // Let it catch up instead of leaving a "Running" row on screen.
            router.refresh();
          }
        }
      } catch {
        // An unreadable poll is not a failed task — the row is still there.
        // The next tick reads it again.
      }

      if (!stopped) {
        timer = setTimeout(read, POLL_MS);
      }
    };

    timer = setTimeout(read, POLL_MS);

    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [open, taskId, live, router]);

  // Follow the answer as it arrives, until the reader takes over by scrolling
  // up — at which point the dialog stops moving under them and stays stopped.
  useEffect(() => {
    const element = viewport.current;

    if (element && following) {
      element.scrollTop = element.scrollHeight;
    }
  }, [turns, activity, task, following]);

  function onScroll() {
    const element = viewport.current;

    if (!element) {
      return;
    }

    const gap = element.scrollHeight - element.scrollTop - element.clientHeight;
    setFollowing(gap < 32);
  }

  function reset() {
    inFlight.current?.abort();
    inFlight.current = null;
    conversation.current = null;

    setTurns([]);
    setDraft("");
    setActivity(null);
    setThinking(false);
    setTask(null);
    setTrouble(null);
    setFollowing(true);
  }

  function nextId(): number {
    counter.current += 1;
    return counter.current;
  }

  /** Take one turn: send what was said and read what the agent does about it. */
  async function say() {
    if (!ready || thinking || task !== null) {
      return;
    }

    const mine = nextId();
    const theirs = nextId();

    setDraft("");
    setTrouble(null);
    setActivity(null);
    setThinking(true);
    setTurns((current) => [
      ...current,
      { id: mine, from: "you", text: written },
      { id: theirs, from: "agent", text: "" },
    ]);

    const abort = new AbortController();
    inFlight.current = abort;
    conversation.current ??= crypto.randomUUID();

    try {
      const response = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: written,
          threadId: conversation.current,
        }),
        signal: abort.signal,
      });

      if (!response.ok || !response.body) {
        setTurns((current) => dropIfUnsaid(current, theirs));
        setTrouble(await unreadable(response));
        return;
      }

      await readTurn(response.body, (event: AgentEvent) => {
        if (event.type === "token") {
          setTurns((current) => appendTo(current, theirs, event.text));
          return;
        }

        if (event.type === "tool") {
          setActivity({ name: event.name, state: event.state });
          return;
        }

        if (event.type === "task") {
          setTask(event.task);
          // The page behind the dialog lists this task now.
          router.refresh();
          return;
        }

        if (event.type === "error") {
          setTrouble(event.message);
        }
      });
    } catch {
      if (!abort.signal.aborted) {
        setTurns((current) => dropIfUnsaid(current, theirs));
        setTrouble(NO_ANSWER);
      }
    } finally {
      inFlight.current = null;
      setThinking(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void say();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends and Shift+Enter breaks the line: this is a message box, not a
    // document.
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void say();
    }
  }

  const line = activity
    ? (TOOL_LINES[activity.name] ?? UNKNOWN_TOOL)[
        activity.state === "started" ? "running" : "done"
      ]
    : null;

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setOpen(next);

        if (!next) {
          // A closed dialog holds nothing: the task it made is in the record,
          // and the next brief starts the conversation over.
          reset();
        }
      }}
    >
      <DialogTrigger
        render={<Button className={cn(className, "cursor-pointer")} />}
      >
        Generate with AI
      </DialogTrigger>

      <DialogContent className="flex max-h-[calc(100dvh-2rem)] flex-col gap-4 sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="type-title">Generate a block</DialogTitle>
        </DialogHeader>

        <div
          ref={viewport}
          onScroll={onScroll}
          className="border-hairline flex min-h-24 flex-1 flex-col gap-4 overflow-y-auto border-y py-4"
        >
          <MessageGroup>
            <Turn from="Generator">{signedIn ? GREETING : VISITOR}</Turn>

            {signedIn
              ? turns.map((turn) => (
                  <Turn
                    key={turn.id}
                    from={turn.from === "you" ? "You" : "Generator"}
                    align={turn.from === "you" ? "end" : "start"}
                  >
                    {turn.from === "agent" && turn.text === "" ? (
                      <span
                        className="text-ink-faint animate-pulse"
                        aria-label="The agent is answering"
                      >
                        …
                      </span>
                    ) : (
                      turn.text
                    )}
                  </Turn>
                ))
              : null}
          </MessageGroup>

          {line ? (
            <p className="type-label text-ink-faint flex items-center gap-2">
              <span
                className={cn(
                  "bg-coral size-1.5 shrink-0 rounded-full",
                  activity?.state === "started" && "animate-pulse",
                )}
                aria-hidden
              />
              <span role="status">{line}</span>
            </p>
          ) : null}
        </div>

        {trouble ? (
          <Alert variant="destructive">
            <AlertTitle>The turn did not finish</AlertTitle>
            <AlertDescription>{trouble}</AlertDescription>
          </Alert>
        ) : null}

        {task ? (
          <div className="border-hairline flex flex-col gap-3 border-t pt-4">
            <div
              className="flex items-baseline justify-between gap-4"
              role="status"
            >
              <span className="type-label text-ink-faint">Checklist</span>
              <StatusWord
                label={TASK_STATUS_LABELS[task.status]}
                running={task.status === "running"}
                failed={task.status === "failed"}
                muted={task.status === "pending"}
              />
            </div>

            <p className="type-body-sm text-ink-muted">
              {QUEUED_LINES[task.status]}
            </p>

            {task.steps.length > 0 ? (
              <TaskChecklist steps={task.steps} />
            ) : (
              <p className="type-meta text-ink-muted">
                No worker has opened this task yet. Its steps are written when
                one claims it.
              </p>
            )}

            {task.error ? (
              <Alert variant="destructive">
                <AlertTitle>The task stopped</AlertTitle>
                <AlertDescription>{task.error}</AlertDescription>
              </Alert>
            ) : null}
          </div>
        ) : null}

        {signedIn && task === null ? (
          <DialogFooter className="sm:justify-between">
            <form onSubmit={onSubmit} className="flex w-full flex-col gap-3">
              <Field>
                <FieldLabel htmlFor="message">Message</FieldLabel>
                <Textarea
                  id="message"
                  name="message"
                  rows={2}
                  value={draft}
                  disabled={thinking}
                  onKeyDown={onKeyDown}
                  onChange={(event) => setDraft(event.target.value)}
                  placeholder="A pricing page for a developer tool: three tiers, an annual toggle, one comparison row per feature."
                />
              </Field>

              <Button
                type="submit"
                className="self-start"
                disabled={!ready || thinking}
              >
                {thinking ? "Answering…" : "Send"}
              </Button>
            </form>
          </DialogFooter>
        ) : null}

        {signedIn && task !== null ? (
          <p className="type-meta text-ink-muted">
            The conversation ends where the task starts: from here the checklist
            is the record, and it keeps writing itself once this dialog closes.
          </p>
        ) : null}

        {signedIn ? null : (
          <DialogFooter className="sm:justify-between">
            <Link
              href="/auth/login?next=%2F"
              prefetch={false}
              className={buttonVariants({ variant: "link" })}
            >
              Sign in
            </Link>
          </DialogFooter>
        )}

        {task ? (
          <DialogFooter className="sm:justify-between">
            {/* Anchors, not buttons: this is navigation, and a link that
                announces itself as a button is a small lie. */}
            <Link
              href={`/tasks/${task.id}`}
              prefetch={false}
              className={buttonVariants({ variant: "link" })}
            >
              Follow the task
            </Link>

            {task.component_id ? (
              <Link
                href={`/?kind=component&item=${task.component_id}`}
                prefetch={false}
                className={buttonVariants({ variant: "link" })}
              >
                Open the block
              </Link>
            ) : null}
          </DialogFooter>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}
