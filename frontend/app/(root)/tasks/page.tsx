import type { Metadata } from "next";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { AgentChatTrigger } from "@/components/vault/agent-chat";
import { StatusWord } from "@/components/vault/status-word";
import { getSession } from "@/server/auth/auth.lib";
import { VaultUnreadable, listTasks } from "@/lib/vault/api";
import { formatDate, formatTime } from "@/lib/vault/format";
import { TASK_STATUS_LABELS } from "@/lib/vault/task-status";
import type { Task } from "@/lib/vault/types";

const LIST_SIZE = 20;

export const metadata: Metadata = {
  title: "Your tasks",
  description:
    "The background work this account has started, and what each step of it is doing.",
};

/**
 * The account's own work.
 *
 * Only the caller's tasks come back — the token decides that, and the page never
 * asks who they are. A visitor with no session is sent to sign in rather than
 * shown an empty list, because an empty list would be a lie about a page that
 * needs an account to mean anything.
 */
export default async function TasksPage() {
  const session = await getSession();

  if (!session) {
    redirect("/auth/login?next=%2Ftasks");
  }

  let tasks: Task[] = [];
  let failure: string | null = null;

  try {
    tasks = (await listTasks(session.session.token, { limit: LIST_SIZE }))
      .items;
  } catch (error) {
    if (!(error instanceof VaultUnreadable)) {
      throw error;
    }

    failure = error.message;
  }

  return (
    <div className="mx-auto w-full max-w-[900px] px-6 py-12">
      <h1 className="sr-only">Your tasks</h1>

      <header className="flex flex-col gap-3">
        <p className="text-muted-foreground max-w-[68ch] text-sm">
          Every block or image handed to the generator becomes one of these. The
          checklist is the task&apos;s own record: a worker writes it as it
          goes, and this page only reads it.
        </p>
      </header>

      {failure ? (
        <Alert variant="destructive" className="mt-10">
          <AlertTitle>The vault did not answer</AlertTitle>
          <AlertDescription>
            <p>
              Nothing is lost: your tasks are kept in the database, not in the
              worker&apos;s memory. Reload to try again.
            </p>
            <p className="mt-2 text-xs">{failure}</p>
          </AlertDescription>
        </Alert>
      ) : tasks.length === 0 ? (
        <Empty className="mt-10 py-20">
          <EmptyHeader>
            <EmptyTitle className="text-lg font-semibold tracking-tight">
              No tasks yet
            </EmptyTitle>
            <EmptyDescription>
              Hand the generator a brief and it will appear here, step by step.
            </EmptyDescription>
          </EmptyHeader>
          <EmptyContent>
            <AgentChatTrigger />
          </EmptyContent>
        </Empty>
      ) : (
        <ul className="border-border mt-10 border-t">
          {tasks.map((task) => (
            <li key={task.id} className="border-border border-b">
              <Link
                href={`/tasks/${task.id}`}
                className="hover:bg-muted/60 grid gap-2 px-1 py-4 transition-colors duration-150 sm:grid-cols-[7rem_minmax(0,1fr)_auto] sm:items-baseline sm:gap-6"
              >
                <StatusWord
                  label={TASK_STATUS_LABELS[task.status]}
                  running={task.status === "running"}
                  failed={task.status === "failed"}
                  muted={task.status === "pending"}
                />

                <span className="text-foreground min-w-0 text-sm">
                  {task.brief}
                </span>

                <span className="text-muted-foreground shrink-0 text-xs tabular-nums">
                  {formatDate(task.created_at)} {formatTime(task.created_at)}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
