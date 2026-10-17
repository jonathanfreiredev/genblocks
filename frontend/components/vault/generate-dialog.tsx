"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent, type ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Bubble, BubbleContent } from "@/components/ui/bubble";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldDescription, FieldLabel } from "@/components/ui/field";
import { Message, MessageContent, MessageGroup } from "@/components/ui/message";
import { Textarea } from "@/components/ui/textarea";
import { StatusWord } from "@/components/vault/status-word";
import { TaskChecklist } from "@/components/vault/task-checklist";
import { TASK_STATUS_LABELS } from "@/lib/vault/task-status";
import type { Task, TaskDetail, TaskStatus } from "@/lib/vault/types";
import { createTaskAction } from "@/server/tasks/tasks.actions";
import { createTaskSchema } from "@/server/tasks/tasks.schemas";

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

/** What the generator says once the brief is its problem. */
const QUEUED_LINES: Record<TaskStatus, string> = {
  pending:
    "Queued. The checklist below is the task's own record, and it fills in once a worker claims it.",
  running: "Running. Each step closes as the worker finishes it.",
  succeeded: "Published, and scored. The block is in the vault.",
  failed: "The task stopped. What it said is below.",
  interrupted:
    "The worker went away mid-run, so this one is unfinished. The record is kept.",
};

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

/**
 * The vault's one action: a brief, and the task it becomes.
 *
 * The conversation is the surface (PLAN.md, decision 5) and it ends where the
 * generation starts — this is not a chat about the collection. It is scripted:
 * no model reads the brief here, and the header says so rather than dressing a
 * template up as an agent. What is real is everything after the answer: the
 * task, its four steps, and the checklist the worker writes them into.
 *
 * `signedIn` is false on the public gallery, where the vault can be read but
 * nothing can be asked for: the account is what a task hangs off, so a visitor
 * is sent to sign in rather than allowed to fill in a brief that would be
 * refused on the way out.
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
  const [phase, setPhase] = useState<"asking" | "confirming" | "queued">(
    "asking",
  );
  const [brief, setBrief] = useState("");
  const [task, setTask] = useState<Task | null>(null);
  const [trouble, setTrouble] = useState<string | null>(null);
  const [queueing, setQueueing] = useState(false);

  const written = brief.trim();
  const parsed = createTaskSchema.safeParse({ brief: written });
  const ready = parsed.success;

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

  function reset() {
    setPhase("asking");
    setBrief("");
    setTask(null);
    setTrouble(null);
  }

  function readBack(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!ready) {
      return;
    }

    setTrouble(null);
    setPhase("confirming");
  }

  async function queue() {
    setQueueing(true);
    setTrouble(null);

    const result = await createTaskAction({ brief: written });

    setQueueing(false);

    if (result?.serverError || !result?.data) {
      setTrouble(
        result?.serverError?.message ??
          "The generator did not answer. Nothing was queued.",
      );
      return;
    }

    setTask(result.data.task);
    setPhase("queued");
    router.refresh();
  }

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
      <DialogTrigger render={<Button className={className} />}>
        Generate with AI
      </DialogTrigger>

      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle className="type-title">Generate a block</DialogTitle>
          <DialogDescription>
            One brief becomes one task, and the checklist is written as the
            worker runs it. No model reads the brief yet: the queue, the four
            steps and the record are real; the block itself is a placeholder.
          </DialogDescription>
        </DialogHeader>

        <MessageGroup>
          <Turn from="Generator">
            {signedIn
              ? "What should I build? A brief: what the block is for, the sections it needs, and anything it must avoid."
              : "Queueing a block needs an account: the task belongs to whoever asks for it, and its record has to be readable by someone. Sign in and the brief is yours."}
          </Turn>

          {signedIn && phase !== "asking" ? (
            <Turn from="You" align="end">
              {written}
            </Turn>
          ) : null}

          {phase === "confirming" ? (
            <Turn from="Generator">
              I will queue this brief as one task. The worker puts four steps
              against it — references, generation, judging, publishing — and
              writes down what each one did.
            </Turn>
          ) : null}

          {task ? (
            <Turn from="Generator">{QUEUED_LINES[task.status]}</Turn>
          ) : null}
        </MessageGroup>

        {trouble ? (
          <Alert variant="destructive">
            <AlertTitle>The brief did not reach the queue</AlertTitle>
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

        {signedIn && phase === "asking" ? (
          <DialogFooter className="sm:justify-between">
            <form onSubmit={readBack} className="flex w-full flex-col gap-3">
              <Field>
                <FieldLabel htmlFor="brief">Brief</FieldLabel>
                <Textarea
                  id="brief"
                  name="brief"
                  rows={3}
                  value={brief}
                  onChange={(event) => setBrief(event.target.value)}
                  placeholder="A pricing page for a developer tool: three tiers, an annual toggle, one comparison row per feature."
                />
                <FieldDescription>
                  10 to 2000 characters. The worker treats the brief as the
                  whole specification.
                </FieldDescription>
              </Field>

              <Button type="submit" className="self-start" disabled={!ready}>
                Answer
              </Button>
            </form>
          </DialogFooter>
        ) : null}

        {phase === "confirming" ? (
          <DialogFooter className="sm:justify-between">
            <Button
              type="button"
              variant="outline"
              disabled={queueing}
              onClick={() => setPhase("asking")}
            >
              Edit the brief
            </Button>
            <Button type="button" disabled={queueing} onClick={queue}>
              {queueing ? "Queueing…" : "Queue the task"}
            </Button>
          </DialogFooter>
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
