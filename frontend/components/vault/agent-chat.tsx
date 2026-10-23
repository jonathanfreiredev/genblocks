"use client";

import {
  ArrowUpIcon,
  CheckIcon,
  CircleAlertIcon,
  CircleIcon,
  SparklesIcon,
  SquarePenIcon,
  SquareIcon,
  XIcon,
} from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import logo from "@/app/icon.png";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  InputGroup,
  InputGroupAddon,
  InputGroupButton,
  InputGroupTextarea,
} from "@/components/ui/input-group";
import { Marker, MarkerContent, MarkerIcon } from "@/components/ui/marker";
import {
  Message,
  MessageAvatar,
  MessageContent,
  MessageHeader,
} from "@/components/ui/message";
import {
  MessageScroller,
  MessageScrollerButton,
  MessageScrollerContent,
  MessageScrollerItem,
  MessageScrollerProvider,
  MessageScrollerViewport,
} from "@/components/ui/message-scroller";
import { Spinner } from "@/components/ui/spinner";
import {
  Trace,
  TraceDescription,
  TraceIcon,
  TraceLine,
  TraceTitle,
} from "@/components/ui/trace";
import { readTurn } from "@/lib/agent/stream";
import { Markdown } from "@/components/vault/markdown";
import { elapsed } from "@/lib/vault/format";
import { TASK_STATUS_LABELS } from "@/lib/vault/task-status";
import type { Suggestion, Task, TaskDetail } from "@/lib/vault/types";
import { MESSAGE_MAX_LENGTH } from "@/lib/agent/limits";
import { SuggestionRail } from "@/components/vault/suggestion-rail";
import { StatusWord } from "@/components/vault/status-word";

/**
 * Where the conversation lives between page loads.
 *
 * The id, not the transcript: the agent's memory is on the other end of this id,
 * and a full transcript in localStorage would be a second, stale copy of it.
 */
const THREAD_KEY = "genblocks-chat-thread";

/** How often a queued task is re-read while a worker is on it. */
const POLL_MS = 1000;

const SUGGESTED_PROMPTS = [
  "What is in the registry?",
  "Find me a pricing block.",
  "What pictures do you have?",
  "Build a hero for a developer tool.",
];

/** What each tool is doing, in the words of the person watching it. */
const TOOL_COPY: Record<string, { running: string; done: string }> = {
  registry_overview: {
    running: "Reading the registry",
    done: "Read the registry",
  },
  search_components: {
    running: "Searching the blocks",
    done: "Searched the blocks",
  },
  find_images: {
    running: "Looking through the pictures",
    done: "Looked through the pictures",
  },
  plan_image: {
    running: "Checking the image prompt",
    done: "Checked the image prompt",
  },
  generate_image: {
    running: "Preparing the image",
    done: "Prepared the image",
  },
  plan_component: {
    running: "Checking the brief",
    done: "Checked the brief",
  },
  create_component: {
    running: "Preparing the brief",
    done: "Prepared the brief",
  },
};

const UNKNOWN_TOOL = { running: "Working", done: "Worked" };

type Activity = {
  id: number;
  name: string;
  state: "started" | "finished";
};

type Proposal = {
  kind: "component" | "image";
  brief: string;
  force: boolean;
  width: number | null;
  height: number | null;
  category: string | null;
};

function proposalKey(proposal: Proposal): string {
  return [
    proposal.kind,
    proposal.brief,
    proposal.force,
    proposal.width,
    proposal.height,
    proposal.category,
  ].join("|");
}

type Turn = {
  id: number;
  from: "you" | "agent";
  text: string;
  activities: Activity[];
  suggestions: Suggestion[];
  proposals: Proposal[];
  taskIds: string[];
  stopped: boolean;
  streaming: boolean;
};

function isLive(status: Task["status"]): boolean {
  return status === "pending" || status === "running";
}

function initials(name: string | null): string {
  const parts = (name ?? "").trim().split(/\s+/).filter(Boolean);

  if (parts.length === 0) {
    return "?";
  }

  return parts
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

/** Add a token to the answer it belongs to. */
function appendText(turns: Turn[], id: number, text: string): Turn[] {
  return turns.map((turn) =>
    turn.id === id ? { ...turn, text: turn.text + text } : turn,
  );
}

/** Record a tool starting or finishing on one answer. */
function recordActivity(turns: Turn[], id: number, activity: Activity): Turn[] {
  return turns.map((turn) => {
    if (turn.id !== id) {
      return turn;
    }

    if (activity.state === "started") {
      return { ...turn, activities: [...turn.activities, activity] };
    }

    // A finished name closes the most recent matching start. The stream sends
    // the two halves separately, and a tool can run twice in one turn.
    let index = -1;
    for (let at = turn.activities.length - 1; at >= 0; at -= 1) {
      const one = turn.activities[at];
      if (one.name === activity.name && one.state === "started") {
        index = at;
        break;
      }
    }

    if (index === -1) {
      return { ...turn, activities: [...turn.activities, activity] };
    }

    const activities = turn.activities.slice();
    activities[index] = { ...activities[index], state: "finished" };

    return { ...turn, activities };
  });
}

/** Keep one card per artifact, however many searches found it. */
function addSuggestions(
  turns: Turn[],
  id: number,
  arriving: Suggestion[],
): Turn[] {
  return turns.map((turn) => {
    if (turn.id !== id) {
      return turn;
    }

    const seen = new Set(
      turn.suggestions.map((one) => `${one.kind}-${one.id}`),
    );

    return {
      ...turn,
      suggestions: [
        ...turn.suggestions,
        ...arriving.filter((one) => !seen.has(`${one.kind}-${one.id}`)),
      ],
    };
  });
}

/** Keep one confirmation card per prepared task. */
function addProposal(turns: Turn[], id: number, proposal: Proposal): Turn[] {
  return turns.map((turn) =>
    turn.id === id &&
    !turn.proposals.some((one) => proposalKey(one) === proposalKey(proposal))
      ? { ...turn, proposals: [...turn.proposals, proposal] }
      : turn,
  );
}

/** Drop a proposal once the person has queued it. */
function removeProposal(turns: Turn[], id: number, proposal: Proposal): Turn[] {
  return turns.map((turn) =>
    turn.id === id
      ? {
          ...turn,
          proposals: turn.proposals.filter(
            (one) => proposalKey(one) !== proposalKey(proposal),
          ),
        }
      : turn,
  );
}

/** Attach a queued task to the answer that queued it. */
function addTask(turns: Turn[], id: number, taskId: string): Turn[] {
  return turns.map((turn) =>
    turn.id === id && !turn.taskIds.includes(taskId)
      ? { ...turn, taskIds: [...turn.taskIds, taskId] }
      : turn,
  );
}

/** Drop an answer that never said anything, so a failure leaves no empty bubble. */
function dropIfUnsaid(turns: Turn[], id: number): Turn[] {
  return turns.filter(
    (turn) =>
      turn.id !== id ||
      turn.text !== "" ||
      turn.activities.length > 0 ||
      turn.suggestions.length > 0 ||
      turn.proposals.length > 0 ||
      turn.taskIds.length > 0,
  );
}

/** What the route handler said when the agent could not be reached. */
async function unreadable(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null);
  const said =
    body && typeof body === "object" && "error" in body
      ? (body as { error: unknown }).error
      : null;

  return typeof said === "string" ? said : "The agent did not answer.";
}

function readThread(): string {
  try {
    const stored = window.localStorage.getItem(THREAD_KEY);
    if (stored && stored.length >= 8) {
      return stored;
    }
  } catch {
    // Private mode or a full quota: a per-session id still works.
  }

  const created = crypto.randomUUID();
  try {
    window.localStorage.setItem(THREAD_KEY, created);
  } catch {
    // The conversation still works for this visit.
  }

  return created;
}

function rememberThread(id: string) {
  try {
    window.localStorage.setItem(THREAD_KEY, id);
  } catch {
    // Nothing to do: the id in memory is still the one this visit uses.
  }
}

function ActivityTrace({ activities }: { activities: Activity[] }) {
  return (
    <Trace className="gap-1.5">
      {activities.map((activity) => {
        const copy = TOOL_COPY[activity.name] ?? UNKNOWN_TOOL;
        const running = activity.state === "started";

        return (
          <TraceLine key={activity.id} status={running ? "running" : undefined}>
            <TraceIcon>
              {running ? (
                <Spinner className="size-3.5" />
              ) : (
                <CheckIcon className="size-3.5" />
              )}
            </TraceIcon>
            <TraceTitle>{running ? copy.running : copy.done}</TraceTitle>
          </TraceLine>
        );
      })}
    </Trace>
  );
}

function StepLine({ step }: { step: Task["steps"][number] }) {
  const status =
    step.status === "running"
      ? "running"
      : step.status === "failed"
        ? "error"
        : step.status === "pending"
          ? "pending"
          : undefined;

  return (
    <TraceLine status={status}>
      <TraceIcon>
        {step.status === "running" ? (
          <Spinner className="size-3.5" />
        ) : step.status === "failed" ? (
          <XIcon className="size-3.5" />
        ) : step.status === "pending" ? (
          <CircleIcon className="size-3" />
        ) : (
          <CheckIcon className="size-3.5" />
        )}
      </TraceIcon>
      <TraceTitle>{step.name}</TraceTitle>
      <TraceDescription>
        {elapsed(step.started_at, step.finished_at)}
      </TraceDescription>
    </TraceLine>
  );
}

function TaskCard({ task }: { task: Task }) {
  const live = isLive(task.status);
  const isImage = task.kind === "generate_image";
  const heading = task.cached
    ? "Already in the registry"
    : task.status === "failed"
      ? isImage
        ? "The image stopped"
        : "The build stopped"
      : task.status === "succeeded"
        ? isImage
          ? "Image published"
          : "Block published"
        : isImage
          ? "Generating the image"
          : "Building the block";

  return (
    <div className="bg-muted/20 mt-1 overflow-hidden rounded-xl border">
      <div className="flex items-start justify-between gap-3 p-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <span className="bg-background mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full">
            {live ? (
              <Spinner className="size-3.5" />
            ) : task.status === "failed" ? (
              <XIcon className="text-destructive size-3.5" />
            ) : (
              <CheckIcon className="size-3.5" />
            )}
          </span>
          <div className="min-w-0">
            <p className="text-sm font-medium">{heading}</p>
            <p className="text-muted-foreground line-clamp-1 text-xs">
              {task.brief}
            </p>
          </div>
        </div>

        <StatusWord
          label={TASK_STATUS_LABELS[task.status]}
          running={live}
          failed={task.status === "failed"}
          muted={task.status === "pending"}
        />
      </div>

      {task.steps.length > 0 ? (
        <Trace className="gap-1 px-3 pb-3">
          {task.steps.map((step) => (
            <StepLine key={step.id} step={step} />
          ))}
        </Trace>
      ) : (
        <p className="text-muted-foreground px-3 pb-3 text-xs">
          Waiting for a worker to open it.
        </p>
      )}

      {task.error ? (
        <p className="text-destructive px-3 pb-2 text-xs">{task.error}</p>
      ) : null}

      <div className="bg-background/50 flex flex-wrap items-center gap-2 border-t px-3 py-2">
        <Link
          href={`/tasks/${task.id}`}
          prefetch={false}
          className={buttonVariants({ variant: "outline", size: "xs" })}
        >
          Follow the task
        </Link>
        {task.component_id ? (
          <Link
            href={`/blocks/${task.component_id}`}
            prefetch={false}
            className={buttonVariants({ size: "xs" })}
          >
            Open the block
          </Link>
        ) : null}
        {task.image_id ? (
          <Link
            href={`/images/${task.image_id}`}
            prefetch={false}
            className={buttonVariants({ size: "xs" })}
          >
            Open the image
          </Link>
        ) : null}
      </div>
    </div>
  );
}

function ProposalCard({
  proposal,
  onQueue,
}: {
  proposal: Proposal;
  onQueue: () => Promise<boolean>;
}) {
  const [pending, setPending] = useState(false);

  async function queue() {
    setPending(true);
    try {
      await onQueue();
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="bg-muted/20 flex flex-col gap-3 rounded-lg border p-3">
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium">
          {proposal.kind === "image"
            ? "Ready to generate this image"
            : proposal.force
              ? "A new version, ready to build"
              : "Ready to build"}
        </p>
        <p className="text-muted-foreground text-sm whitespace-pre-wrap">
          {proposal.brief}
        </p>
        {proposal.kind === "image" ? (
          <p className="text-muted-foreground text-xs tabular-nums">
            {proposal.width} × {proposal.height} · {proposal.category}
          </p>
        ) : null}
      </div>
      <div className="flex justify-end">
        <Button
          type="button"
          size="sm"
          onClick={() => void queue()}
          disabled={pending}
        >
          {pending ? (
            <Spinner data-icon="inline-start" />
          ) : (
            <SparklesIcon data-icon="inline-start" />
          )}
          {proposal.kind === "image" ? "Generate image" : "Queue block"}
        </Button>
      </div>
    </div>
  );
}

function TurnView({
  turn,
  tasks,
  userName,
  onOpenItem,
  onQueue,
}: {
  turn: Turn;
  tasks: Record<string, Task>;
  userName: string | null;
  onOpenItem: () => void;
  onQueue: (proposal: Proposal) => Promise<boolean>;
}) {
  const mine = turn.from === "you";
  const waiting =
    !mine &&
    turn.streaming &&
    !turn.text &&
    !turn.stopped &&
    turn.activities.length === 0 &&
    turn.suggestions.length === 0 &&
    turn.proposals.length === 0 &&
    turn.taskIds.length === 0;

  return (
    <Message align={mine ? "end" : "start"}>
      <MessageAvatar className="size-8 self-start">
        {mine ? (
          <span className="text-[0.65rem] font-medium">
            {initials(userName)}
          </span>
        ) : (
          <SparklesIcon className="size-3.5" />
        )}
      </MessageAvatar>

      <MessageContent>
        <MessageHeader>{mine ? "You" : "GenBlocks"}</MessageHeader>

        {!mine && turn.activities.length > 0 ? (
          <ActivityTrace activities={turn.activities} />
        ) : null}

        {turn.text ? (
          <Bubble
            variant={mine ? "default" : "ghost"}
            align={mine ? "end" : "start"}
          >
            <BubbleContent className={mine ? "whitespace-pre-wrap" : undefined}>
              {mine ? (
                turn.text
              ) : (
                <Markdown streaming={turn.streaming}>{turn.text}</Markdown>
              )}
            </BubbleContent>
          </Bubble>
        ) : waiting ? (
          <Marker role="status" className="py-0.5">
            <MarkerIcon>
              <Spinner />
            </MarkerIcon>
            <MarkerContent>Thinking…</MarkerContent>
          </Marker>
        ) : null}

        {turn.stopped ? (
          <Marker className="py-0.5">
            <MarkerContent>Stopped.</MarkerContent>
          </Marker>
        ) : null}

        {turn.suggestions.length > 0 ? (
          <SuggestionRail items={turn.suggestions} onOpenItem={onOpenItem} />
        ) : null}

        {turn.proposals.map((proposal) => (
          <ProposalCard
            key={proposal.brief}
            proposal={proposal}
            onQueue={() => onQueue(proposal)}
          />
        ))}

        {turn.taskIds.map((id) =>
          tasks[id] ? <TaskCard key={id} task={tasks[id]} /> : null,
        )}
      </MessageContent>
    </Message>
  );
}

function Welcome({
  signedIn,
  onPrompt,
}: {
  signedIn: boolean;
  onPrompt: (prompt: string) => void;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-5 px-6 py-10 text-center">
      <Image
        src={logo}
        alt=""
        width={48}
        height={48}
        className="size-12 shrink-0 rounded-xl"
      />

      <div className="flex max-w-sm flex-col gap-1.5">
        <h3 className="text-base font-semibold">
          Ask about anything in the vault
        </h3>
        <p className="text-muted-foreground text-sm">
          Find a block, look through the pictures, describe a block to build, or
          ask for a new image.
        </p>
        <p className="text-muted-foreground text-xs">
          This is an AI assistant. It can be wrong.
        </p>
      </div>

      {signedIn ? (
        <div className="flex max-w-md flex-wrap justify-center gap-2">
          {SUGGESTED_PROMPTS.map((prompt) => (
            <Button
              key={prompt}
              type="button"
              variant="outline"
              size="sm"
              className="h-auto rounded-full py-1.5 text-left whitespace-normal"
              onClick={() => onPrompt(prompt)}
            >
              {prompt}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

/**
 * The heavy half of the assistant: transcript, stream, proposals and the dialog.
 *
 * It is loaded dynamically by `agent-chat-context` on the first click, so a
 * catalogue visit does not download Streamdown and Shiki for a surface the
 * visitor may never open.
 */
export function AgentChatDialog({
  open,
  onOpenChange,
  signedIn = true,
  userName = null,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  signedIn?: boolean;
  userName?: string | null;
}) {
  const router = useRouter();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [tasks, setTasks] = useState<Record<string, Task>>({});
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [trouble, setTrouble] = useState<string | null>(null);

  const counter = useRef(0);
  const thread = useRef<string | null>(null);
  const inFlight = useRef<AbortController | null>(null);
  const activeTurn = useRef<number | null>(null);
  const tasksRef = useRef(tasks);

  const written = draft.trim();
  const ready = written.length > 0 && written.length <= MESSAGE_MAX_LENGTH;

  const liveKey = Object.values(tasks)
    .filter((task) => isLive(task.status))
    .map((task) => task.id)
    .sort()
    .join(",");

  function nextId(): number {
    counter.current += 1;
    return counter.current;
  }

  function threadFor(): string {
    if (!thread.current) {
      thread.current = readThread();
    }

    return thread.current;
  }

  function startNew() {
    inFlight.current?.abort();
    inFlight.current = null;
    activeTurn.current = null;

    const id = crypto.randomUUID();
    thread.current = id;
    rememberThread(id);

    setThinking(false);
    setTurns([]);
    setTasks({});
    setTrouble(null);
    setDraft("");
  }

  function stop() {
    const id = activeTurn.current;
    inFlight.current?.abort();
    inFlight.current = null;
    activeTurn.current = null;
    setThinking(false);

    if (id !== null) {
      setTurns((current) =>
        current.map((turn) =>
          turn.id === id ? { ...turn, stopped: true, streaming: false } : turn,
        ),
      );
    }
  }

  // A turn that is still being read when the component goes away has no reader.
  useEffect(() => {
    return () => {
      const current = inFlight.current;
      inFlight.current = null;
      current?.abort();
    };
  }, []);

  // Keep the latest tasks where the poll can read them without restarting on
  // every status word.
  useEffect(() => {
    tasksRef.current = tasks;
  }, [tasks]);

  // Poll the queued tasks while a worker has them. The task card is the record;
  // this only keeps it current.
  useEffect(() => {
    if (!liveKey) {
      return;
    }

    let stopped = false;

    const tick = async () => {
      const live = Object.values(tasksRef.current).filter((task) =>
        isLive(task.status),
      );
      if (live.length === 0) {
        return;
      }

      const next = await Promise.all(
        live.map(async (task) => {
          try {
            const response = await fetch(`/api/tasks/${task.id}`, {
              cache: "no-store",
            });

            return response.ok ? ((await response.json()) as TaskDetail) : null;
          } catch {
            // An unreadable poll is not a failed task: the next tick reads it
            // again, and the row is still there.
            return null;
          }
        }),
      );

      if (stopped) {
        return;
      }

      const finished = next.some((task) => task && !isLive(task.status));

      setTasks((current) => {
        const updated = { ...current };

        for (const task of next) {
          if (task) {
            updated[task.id] = task;
          }
        }

        return updated;
      });

      if (finished) {
        // The page behind the dialog renders the same task. Let it catch up
        // instead of leaving a "Running" row on screen.
        router.refresh();
      }
    };

    const timer = setInterval(tick, POLL_MS);

    return () => {
      stopped = true;
      clearInterval(timer);
    };
  }, [liveKey, router]);

  async function confirmProposal(
    turnId: number,
    proposal: Proposal,
  ): Promise<boolean> {
    setTrouble(null);

    try {
      const response = await fetch("/api/agent/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(proposal),
      });

      if (!response.ok) {
        setTrouble(await unreadable(response));
        return false;
      }

      const task = (await response.json()) as Task;
      setTasks((current) => ({ ...current, [task.id]: task }));
      setTurns((current) =>
        addTask(removeProposal(current, turnId, proposal), turnId, task.id),
      );
      router.refresh();

      return true;
    } catch {
      setTrouble("The task could not be queued. Nothing was created.");
      return false;
    }
  }

  async function say(text?: string) {
    const message = (text ?? draft).trim();

    if (!signedIn || thinking || message.length === 0) {
      return;
    }

    if (message.length > MESSAGE_MAX_LENGTH) {
      return;
    }

    const mine = nextId();
    const theirs = nextId();

    setDraft("");
    setTrouble(null);
    setThinking(true);
    activeTurn.current = theirs;
    setTurns((current) => [
      ...current,
      {
        id: mine,
        from: "you",
        text: message,
        activities: [],
        suggestions: [],
        proposals: [],
        taskIds: [],
        stopped: false,
        streaming: false,
      },
      {
        id: theirs,
        from: "agent",
        text: "",
        activities: [],
        suggestions: [],
        proposals: [],
        taskIds: [],
        stopped: false,
        streaming: true,
      },
    ]);

    const controller = new AbortController();
    inFlight.current = controller;

    try {
      const response = await fetch("/api/agent/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          threadId: threadFor(),
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        setTurns((current) => dropIfUnsaid(current, theirs));
        setTrouble(await unreadable(response));
        return;
      }

      await readTurn(response.body, (event) => {
        if (event.type === "token") {
          setTurns((current) => appendText(current, theirs, event.text));
          return;
        }

        if (event.type === "tool") {
          const activity: Activity = {
            id: nextId(),
            name: event.name,
            state: event.state,
          };
          setTurns((current) => recordActivity(current, theirs, activity));
          return;
        }

        if (event.type === "suggestions") {
          setTurns((current) => addSuggestions(current, theirs, event.items));
          return;
        }

        if (event.type === "proposal") {
          setTurns((current) =>
            addProposal(current, theirs, {
              kind: event.kind,
              brief: event.brief,
              force: event.force,
              width: event.width,
              height: event.height,
              category: event.category,
            }),
          );
          return;
        }

        if (event.type === "task") {
          setTasks((current) => ({
            ...current,
            [event.task.id]: event.task,
          }));
          setTurns((current) => addTask(current, theirs, event.task.id));
          router.refresh();
          return;
        }

        if (event.type === "error") {
          setTrouble(event.message);
        }
      });
    } catch {
      if (!controller.signal.aborted) {
        setTurns((current) => dropIfUnsaid(current, theirs));
        setTrouble("The agent did not answer.");
      }
    } finally {
      // A turn that was replaced (a new chat) or stopped has already said its
      // own last word; only the turn still holding the controller finishes here.
      if (inFlight.current === controller) {
        inFlight.current = null;
        activeTurn.current = null;
        setThinking(false);
        setTurns((current) =>
          dropIfUnsaid(
            current.map((turn) =>
              turn.id === theirs ? { ...turn, streaming: false } : turn,
            ),
            theirs,
          ),
        );
      }
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void say();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.nativeEvent.isComposing) {
      return;
    }

    // Enter sends and Shift+Enter breaks the line: this is a message box, not a
    // document.
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void say();
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[calc(100dvh-1rem)] max-h-[calc(100dvh-1rem)] flex-col gap-0 overflow-hidden p-0 sm:h-[min(88svh,760px)] sm:max-h-[min(88svh,760px)] sm:max-w-3xl">
        <DialogHeader className="flex shrink-0 flex-row items-center gap-3 border-b px-4 py-3 pr-12">
          <Image
            src={logo}
            alt=""
            width={32}
            height={32}
            className="size-8 shrink-0 rounded-lg"
          />

          <div className="flex min-w-0 flex-1 flex-col">
            <DialogTitle className="truncate text-sm font-semibold">
              Ask AI
            </DialogTitle>
            <DialogDescription className="truncate text-xs">
              Blocks, stock images, or a brief to build.
            </DialogDescription>
          </div>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={startNew}
            aria-label="Start a new conversation"
            className="shrink-0"
          >
            <SquarePenIcon data-icon="inline-start" />
            New chat
          </Button>
        </DialogHeader>

        <div className="min-h-0 flex-1">
          {turns.length === 0 ? (
            <Welcome
              signedIn={signedIn}
              onPrompt={(prompt) => void say(prompt)}
            />
          ) : (
            <MessageScrollerProvider autoScroll>
              <MessageScroller>
                <MessageScrollerViewport>
                  <MessageScrollerContent className="p-4">
                    {turns.map((turn) => (
                      <MessageScrollerItem
                        key={turn.id}
                        messageId={String(turn.id)}
                        scrollAnchor={turn.from === "you"}
                      >
                        <TurnView
                          turn={turn}
                          tasks={tasks}
                          userName={userName}
                          onOpenItem={() => onOpenChange(false)}
                          onQueue={(proposal) =>
                            confirmProposal(turn.id, proposal)
                          }
                        />
                      </MessageScrollerItem>
                    ))}

                    {trouble ? (
                      <MessageScrollerItem>
                        <Marker role="alert" className="text-destructive">
                          <MarkerIcon>
                            <CircleAlertIcon />
                          </MarkerIcon>
                          <MarkerContent>{trouble}</MarkerContent>
                        </Marker>
                      </MessageScrollerItem>
                    ) : null}
                  </MessageScrollerContent>
                </MessageScrollerViewport>

                <MessageScrollerButton />
              </MessageScroller>
            </MessageScrollerProvider>
          )}
        </div>

        {turns.length === 0 && trouble ? (
          <div className="px-4 pb-2">
            <Marker role="alert" className="text-destructive">
              <MarkerIcon>
                <CircleAlertIcon />
              </MarkerIcon>
              <MarkerContent>{trouble}</MarkerContent>
            </Marker>
          </div>
        ) : null}

        {signedIn ? (
          <form onSubmit={onSubmit} className="shrink-0 border-t p-3">
            <InputGroup className="h-auto rounded-xl">
              <InputGroupTextarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                onKeyDown={onKeyDown}
                rows={2}
                maxLength={MESSAGE_MAX_LENGTH}
                disabled={thinking}
                aria-label="Message"
                placeholder="Ask about a block or image, or what to build…"
                className="max-h-40 min-h-14 py-3"
              />
              <InputGroupAddon align="block-end" className="p-2">
                <span className="text-muted-foreground me-auto hidden text-xs sm:block">
                  Enter to send · Shift+Enter for a new line
                </span>

                {thinking ? (
                  <InputGroupButton
                    type="button"
                    size="icon-sm"
                    onClick={stop}
                    aria-label="Stop answering"
                  >
                    <SquareIcon />
                  </InputGroupButton>
                ) : (
                  <InputGroupButton
                    type="submit"
                    size="icon-sm"
                    disabled={!ready}
                    aria-label="Send"
                  >
                    <ArrowUpIcon />
                  </InputGroupButton>
                )}
              </InputGroupAddon>
            </InputGroup>
          </form>
        ) : (
          <div className="shrink-0 border-t p-3">
            <div className="bg-muted/30 flex flex-col gap-2 rounded-xl border p-3 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-muted-foreground text-sm">
                The assistant needs an account: the conversation belongs to
                whoever asks. Sign in to ask about blocks and images, build one,
                or generate an image.
              </p>
              <Link
                href="/auth/login?next=%2Fblocks"
                prefetch={false}
                className={buttonVariants({ variant: "default", size: "sm" })}
              >
                Sign in
              </Link>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
