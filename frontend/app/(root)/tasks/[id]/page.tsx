import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import type { ReactNode } from "react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { StatusWord } from "@/components/vault/status-word";
import { TaskChecklist } from "@/components/vault/task-checklist";
import { TaskResult } from "@/components/vault/task-result";
import { getSession } from "@/server/auth/auth.lib";
import { VaultUnreadable, getTask } from "@/lib/vault/api";
import { formatDate, formatTime } from "@/lib/vault/format";
import { TASK_STATUS_LABELS } from "@/lib/vault/task-status";
import type { TaskDetail } from "@/lib/vault/types";

export const metadata: Metadata = {
  title: "Task",
  description: "One task's checklist and the result it produced.",
};

function Meta({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline gap-2">
      <dt className="type-label text-ink-faint">{label}</dt>
      <dd className="type-meta text-ink-soft max-w-[24ch] truncate">
        {children}
      </dd>
    </div>
  );
}

function stamp(start: string | null): string {
  return start ? `${formatDate(start)} ${formatTime(start)}` : "—";
}

/**
 * One task, read from the record it keeps for itself.
 *
 * The brief is the heading because the brief is what was asked for; the
 * checklist underneath is the answer in progress. A task that is not this
 * caller's is indistinguishable from one that does not exist, which is the rule
 * the service enforces and this page simply obeys.
 */
export default async function TaskPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const session = await getSession();

  if (!session) {
    redirect(`/auth/login?next=${encodeURIComponent(`/tasks/${id}`)}`);
  }

  let task: TaskDetail | null = null;
  let failure: string | null = null;

  try {
    task = await getTask(session.session.token, id);
  } catch (error) {
    if (!(error instanceof VaultUnreadable)) {
      throw error;
    }

    failure = error.message;
  }

  if (!failure && !task) {
    notFound();
  }

  // One artifact per task: what the run produced, published or refused. It is
  // the only place a run that published nothing can be read at all.
  const generation = task?.generations.at(-1) ?? null;

  return (
    <div className="mx-auto w-full max-w-[900px] px-6 py-12">
      {failure ? (
        <Alert variant="destructive">
          <AlertTitle>The vault did not answer</AlertTitle>
          <AlertDescription>
            <p>
              Nothing is lost: the task is kept in the database, not in the
              worker&apos;s memory. Reload to try again.
            </p>
            <p className="type-meta mt-2">{failure}</p>
          </AlertDescription>
        </Alert>
      ) : null}

      {task ? (
        <>
          <h1 className="type-title max-w-[68ch] text-balance">{task.brief}</h1>

          <dl className="border-rule mt-5 flex flex-wrap items-baseline gap-x-8 gap-y-3 border-y py-4">
            <Meta label="Status">
              <StatusWord
                label={TASK_STATUS_LABELS[task.status]}
                running={task.status === "running"}
                failed={task.status === "failed"}
                muted={task.status === "pending"}
              />
            </Meta>
            <Meta label="Queued">{stamp(task.created_at)}</Meta>
            <Meta label="Finished">{stamp(task.finished_at)}</Meta>
            <Meta label="Trace">
              {task.langfuse_trace_id ?? "Not recorded"}
            </Meta>
          </dl>

          {task.error ? (
            <Alert variant="destructive" className="mt-8">
              <AlertTitle>The task stopped</AlertTitle>
              <AlertDescription>{task.error}</AlertDescription>
            </Alert>
          ) : null}

          <h2 className="type-label text-ink-faint mt-10">Checklist</h2>
          <TaskChecklist steps={task.steps} className="mt-3" />

          {generation ? (
            <>
              <h2 className="type-label text-ink-faint mt-10">The result</h2>
              <div className="mt-3">
                <TaskResult generation={generation} brief={task.brief} />
              </div>
            </>
          ) : null}

          {task.component_id ? (
            <p className="mt-10">
              <Button
                variant="link"
                render={
                  <Link
                    href={`/?kind=component&item=${task.component_id}`}
                    prefetch={false}
                  />
                }
              >
                The block this task produced
              </Button>
            </p>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
