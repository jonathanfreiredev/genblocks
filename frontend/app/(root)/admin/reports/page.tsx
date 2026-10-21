import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { ReportDecision } from "@/components/reports/report-decision";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { formatDate, formatTime } from "@/lib/vault/format";
import {
  REPORT_REASONS,
  REPORT_STATUS_LABELS,
  type ReportStatus,
} from "@/lib/reports/types";
import { listReports, ReportsUnreadable } from "@/lib/reports/api";
import { getSession } from "@/server/auth/auth.lib";

const LIST_SIZE = 50;

const STATUSES: { value: ReportStatus | "all"; label: string }[] = [
  { value: "open", label: "Open" },
  { value: "reviewing", label: "Reviewing" },
  { value: "resolved", label: "Resolved" },
  { value: "dismissed", label: "Dismissed" },
  { value: "all", label: "All" },
];

export const metadata: Metadata = {
  title: "Reports",
  description: "The human review queue for reported blocks and images.",
};

function statusFrom(
  value: string | string[] | undefined,
): ReportStatus | undefined {
  if (typeof value !== "string") return undefined;
  if (Object.hasOwn(REPORT_STATUS_LABELS, value)) {
    return value as ReportStatus;
  }
  return undefined;
}

/**
 * The operator queue. A report is reviewed against the public page, not against
 * a database row: the item link is the first thing in every card because the
 * decision is about what a visitor sees.
 */
export default async function ReportsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const session = await getSession();

  if (!session) {
    redirect("/auth/login?next=%2Fadmin%2Freports");
  }
  if (!session.user.isAdmin) {
    notFound();
  }

  const params = await searchParams;
  // The queue opens on the work that still needs a person. "All" is an explicit
  // filter, not the absence of one.
  const requested = typeof params.status === "string" ? params.status : "open";
  const active =
    requested === "all" ? undefined : (statusFrom(requested) ?? "open");
  let reports = null;
  let failure: string | null = null;

  try {
    reports = await listReports(session.session.token, {
      status: active,
      limit: LIST_SIZE,
    });
  } catch (error) {
    if (!(error instanceof ReportsUnreadable)) {
      throw error;
    }
    failure = error.message;
  }

  return (
    <div className="mx-auto flex w-full max-w-[960px] flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-2">
          <p className="text-muted-foreground text-xs font-medium tracking-[0.05em] uppercase">
            Operate
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
          <p className="text-muted-foreground max-w-[62ch] text-sm">
            Every report is a request for a person to look. Taking an item down
            permanently removes it and its Cloudinary asset; the report keeps a
            snapshot and its note for the record.
          </p>
        </div>
        {reports ? (
          <Badge variant="outline" className="w-fit tabular-nums">
            {reports.total} {reports.total === 1 ? "report" : "reports"}
          </Badge>
        ) : null}
      </header>

      <nav aria-label="Filter reports" className="flex flex-wrap gap-2">
        {STATUSES.map((status) => {
          const selected =
            status.value === "all"
              ? active === undefined
              : active === status.value;
          return (
            <Link
              key={status.value}
              href={
                status.value === "all"
                  ? "/admin/reports?status=all"
                  : `/admin/reports?status=${status.value}`
              }
              className={cn(
                buttonVariants({
                  variant: selected ? "secondary" : "ghost",
                  size: "sm",
                }),
              )}
              aria-current={selected ? "page" : undefined}
            >
              {status.label}
            </Link>
          );
        })}
      </nav>

      {failure ? (
        <Alert variant="destructive">
          <AlertTitle>The queue did not answer</AlertTitle>
          <AlertDescription>{failure}</AlertDescription>
        </Alert>
      ) : !reports || reports.items.length === 0 ? (
        <Empty className="border-border border-t py-16">
          <EmptyHeader>
            <EmptyTitle>Nothing in this queue</EmptyTitle>
            <EmptyDescription>
              A report for a block or an image arrives here. An empty queue is
              the ordinary state.
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ul className="flex flex-col gap-4">
          {reports.items.map((report) => {
            const reason =
              REPORT_REASONS.find((one) => one.value === report.reason)
                ?.label ?? report.reason;
            const href =
              report.target_kind === "component"
                ? `/blocks/${report.target_slug ?? report.target_id}`
                : `/images/${report.target_slug ?? report.target_id}`;

            return (
              <li key={report.id}>
                <Card>
                  <CardHeader>
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline" className="capitalize">
                        {report.target_kind}
                      </Badge>
                      <Badge
                        variant={
                          report.status === "open"
                            ? "default"
                            : report.status === "reviewing"
                              ? "secondary"
                              : "outline"
                        }
                      >
                        {REPORT_STATUS_LABELS[report.status]}
                      </Badge>
                    </div>
                    <CardTitle>
                      <Link
                        href={href}
                        className="underline-offset-4 hover:underline"
                      >
                        {report.target_title ?? "Removed item"}
                      </Link>
                    </CardTitle>
                    <CardDescription className="flex flex-wrap gap-x-2 gap-y-1">
                      <span>{reason}</span>
                      <span aria-hidden>·</span>
                      <span>{report.reporter ?? "Anonymous"}</span>
                      <span aria-hidden>·</span>
                      <span className="tabular-nums">
                        {formatDate(report.created_at)}{" "}
                        {formatTime(report.created_at)}
                      </span>
                    </CardDescription>
                  </CardHeader>

                  <CardContent className="flex flex-col gap-4">
                    {report.details ? (
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">
                        {report.details}
                      </p>
                    ) : (
                      <p className="text-muted-foreground text-sm">
                        No note was left with the report.
                      </p>
                    )}

                    {report.resolution ? (
                      <>
                        <Separator />
                        <p className="text-sm">
                          <span className="text-muted-foreground">
                            Operator note:{" "}
                          </span>
                          {report.resolution}
                        </p>
                      </>
                    ) : null}

                    {report.status === "open" ||
                    report.status === "reviewing" ? (
                      <>
                        <Separator />
                        <ReportDecision reportId={report.id} />
                      </>
                    ) : null}
                  </CardContent>
                </Card>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
