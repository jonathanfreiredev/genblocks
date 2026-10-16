"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { CircleCheck, Clock, Lock, Play, TriangleAlert } from "lucide-react";

import { WakeNotice } from "@/components/demo/wake-notice";
import { useDemoWake } from "@/components/demo/wake-provider";
import { Button, buttonVariants } from "@/components/ui/button";
import { sleep } from "@/lib/demo-wake";
import { cn } from "@/lib/utils";
import { runDemoAction } from "@/server/demo/demo.actions";
import type {
  DemoRun,
  DemoRunRequest,
  DemoToolCall,
} from "@/server/demo/demo.schemas";

/** How long to leave between two attempts while the demo's services come up. */
const RETRY_INTERVAL_MS = 3_000;

/**
 * How long a visitor waits for the services before the page stops trying and says so.
 *
 * Generous, because two containers can be starting one after the other: the API has
 * to answer before it can wake the MCP. A click that quietly resolves after a minute
 * beats a click that has to be repeated.
 */
const WAIT_FOR_SERVICES_MS = 90_000;

/**
 * A step's own verdict: it answered, or it did not.
 *
 * The icon carries the news and the words stay in the foreground colour. Small
 * text in the destructive hue would sit under the contrast floor, so the red is
 * spent on the mark and the border instead.
 */
function Outcome({ call }: { call: DemoToolCall }) {
  if (call.pending) {
    return (
      <>
        <Clock
          className="text-muted-foreground size-4 shrink-0"
          aria-hidden="true"
        />
        <span className="sr-only">Waiting for you.</span>
      </>
    );
  }

  if (call.result) {
    return (
      <>
        <CircleCheck
          className="text-muted-foreground size-4 shrink-0"
          aria-hidden="true"
        />
        <span className="sr-only">Answered.</span>
      </>
    );
  }

  return (
    <>
      <TriangleAlert
        className="text-destructive size-4 shrink-0"
        aria-hidden="true"
      />
      <span className="sr-only">Did not answer.</span>
    </>
  );
}

/** A run that went wrong, said in the destructive language rather than as a note. */
function Problem({
  title,
  detail,
  children,
}: {
  title: string;
  detail: string;
  children: React.ReactNode;
}) {
  return (
    <div
      role="alert"
      className="border-destructive/40 mt-8 flex gap-3 rounded-xl border p-5"
    >
      <TriangleAlert
        className="text-destructive mt-0.5 size-4 shrink-0"
        aria-hidden="true"
      />
      <div className="space-y-1.5">
        <h2 className="text-sm font-medium">{title}</h2>
        <p className="text-muted-foreground text-sm text-pretty">{children}</p>
        {/* The raw message, kept apart from the sentence that explains it. */}
        <p className="text-muted-foreground font-mono text-xs">{detail}</p>
      </div>
    </div>
  );
}

/**
 * The playground.
 *
 * Three tools, run for real against the MCP server with whoever is looking at the
 * page: two live in the agent's own code, and one of those stops the run to ask the
 * visitor something, while the third is the server's. An anonymous visitor gets the
 * door in their face, which is the point.
 *
 * The services behind it may have been asleep when the visitor arrived. Waking them
 * is this component's job as much as the page's: a run attempts the call, waits for
 * them to come up and attempts it again, so the wait lands on a click that was going
 * to happen anyway.
 */
export function Playground() {
  const { check, note } = useDemoWake();
  const [run, setRun] = useState<DemoRun | null>(null);
  const [problem, setProblem] = useState<{
    title: string;
    detail: string;
  } | null>(null);
  const [isRunning, startRun] = useTransition();

  function execute(input: DemoRunRequest = {}) {
    setProblem(null);

    startRun(async () => {
      // A run can be asked for again; a decision cannot. So the first request waits
      // for the services and repeats itself, while an answer given to a stopped run
      // goes out once: repeating it would apply the same answer twice, and asking the
      // visitor to answer again is the honest thing to do instead.
      const mayWait = input.decision === undefined;
      const deadline = Date.now() + WAIT_FOR_SERVICES_MS;

      for (;;) {
        const result = await runDemoAction(input);

        if (result?.data) {
          setRun(result.data);
          // Both services answered, whatever the page believed a moment ago.
          note("ready");
          return;
        }

        const error = result?.serverError;
        const waking = error?.reason === "service_waking";

        if (!mayWait || !waking || Date.now() > deadline) {
          setProblem(
            waking
              ? {
                  title: "The demo did not come up",
                  detail: error?.message ?? "The API did not answer.",
                }
              : {
                  title: "The run did not reach the server",
                  detail: error?.message ?? "The run did not come back.",
                },
          );
          return;
        }

        note("waking");
        check();
        await sleep(RETRY_INTERVAL_MS);
      }
    });
  }

  function decide(decision: "accept" | "reject") {
    execute({ thread_id: run?.thread_id ?? undefined, decision });
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <Button
          type="button"
          size="lg"
          className="h-10"
          onClick={() => execute()}
          disabled={isRunning}
        >
          <Play className="size-4" />
          {isRunning ? "Running" : run ? "Run it again" : "Run the agent"}
        </Button>
        <p className="text-muted-foreground font-mono text-xs">
          no model is called here
        </p>
      </div>

      {/* Where the button is, so that whoever is about to press it knows what they
          are waiting for. It renders nothing once the demo is up. */}
      <WakeNotice className="mt-4" />

      {problem ? (
        <Problem title={problem.title} detail={problem.detail}>
          Nothing was executed, so nothing below reflects this attempt.
        </Problem>
      ) : null}

      {run ? (
        <div>
          {run.calls.length ? (
            <ol className="divide-border/70 border-border/70 divide-y border-t">
              {run.calls.map((call, index) => (
                <li key={`${call.name}-${index}`} className="space-y-3 py-5">
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                    <Outcome call={call} />
                    <span className="text-muted-foreground font-mono text-xs">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="font-mono text-sm font-medium">
                      {call.name}
                    </span>
                    <span className="text-muted-foreground text-xs">
                      {call.source === "agent"
                        ? "the agent's own tool"
                        : "the MCP server"}
                    </span>
                  </div>

                  {call.result ? (
                    <pre className="border-border overflow-x-auto rounded-lg border p-4 font-mono text-xs leading-6">
                      {JSON.stringify(call.result, null, 2)}
                    </pre>
                  ) : null}

                  {call.error ? (
                    <p className="text-sm text-pretty">{call.error}</p>
                  ) : null}

                  {call.pending ? (
                    <div className="space-y-3">
                      <p className="text-sm text-pretty">{run.approval}</p>
                      <div className="flex flex-wrap gap-3">
                        <Button
                          type="button"
                          size="lg"
                          className="h-10"
                          disabled={isRunning}
                          onClick={() => decide("accept")}
                        >
                          Accept
                        </Button>
                        <Button
                          type="button"
                          variant="outline"
                          size="lg"
                          className="h-10"
                          disabled={isRunning}
                          onClick={() => decide("reject")}
                        >
                          Reject
                        </Button>
                      </div>
                    </div>
                  ) : null}
                </li>
              ))}
            </ol>
          ) : null}

          {run.refused ? (
            <div className="border-border mt-8 flex gap-3 rounded-xl border p-5">
              <Lock
                className="text-muted-foreground mt-0.5 size-4 shrink-0"
                aria-hidden="true"
              />
              <div className="space-y-3">
                <h2 className="text-sm font-medium">
                  The server would not let the run in
                </h2>
                <p className="text-muted-foreground text-sm text-pretty">
                  {run.refused} The tools on the server need a token, and the
                  token comes from your account, so the door stays shut until
                  you sign in.
                </p>
                <Link
                  href="/auth/login"
                  className={cn(buttonVariants({ size: "lg" }), "h-10")}
                >
                  Sign in and run it again
                </Link>
              </div>
            </div>
          ) : null}

          {run.failed ? (
            <Problem title="A tool broke" detail={run.failed}>
              This is not the door refusing, which is the other thing you will
              see here: it is a tool that ran and did not finish.
            </Problem>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
