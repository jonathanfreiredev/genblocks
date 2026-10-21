import { formatDate } from "@/lib/vault/format";

function Row({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-t py-2.5 first:border-t-0">
      <dt className="text-muted-foreground shrink-0 text-sm">{label}</dt>
      <dd className="text-foreground min-w-0 truncate text-sm font-medium">
        {children}
      </dd>
    </div>
  );
}

/**
 * The facts about one artifact, in the order a reader asks for them: what it
 * is, when it joined, what made it, and where the run can be read.
 *
 * It sits above the scores in the evidence panel rather than beside them, which
 * is why the trace is a row here and not a section of its own. A block puts its
 * title here, below the render: the picture is the first thing, and the prompt
 * tab already carries the brief, so repeating it above the facts would be a
 * second copy.
 */
export function ItemDetails({
  title,
  category,
  date,
  model,
  traceId,
  provenance,
}: {
  title?: string | null;
  category: string;
  date: string;
  model: string | null;
  traceId: string | null;
  provenance?: Record<string, unknown> | null;
}) {
  const host = process.env.NEXT_PUBLIC_LANGFUSE_HOST?.replace(/\/+$/, "");
  const traceUrl = host && traceId ? `${host}/trace/${traceId}` : null;

  return (
    <div className="flex flex-col gap-4">
      {title ? (
        <h1 className="text-base font-semibold tracking-tight text-balance">
          {title}
        </h1>
      ) : null}

      <dl className="flex flex-col">
        <Row label="Category">{category}</Row>
        <Row label="Date">{formatDate(date)}</Row>
        <Row label="Model">{model ?? "No model ran"}</Row>
        <Row label="Source">
          {provenance?.digital_source_type === "trainedAlgorithmicMedia"
            ? "AI-generated"
            : "Not recorded"}
        </Row>
        <Row label="Trace">
          {traceUrl ? (
            <a
              href={traceUrl}
              target="_blank"
              rel="noreferrer"
              aria-label="Open the trace in Langfuse"
              className="underline-offset-4 hover:underline"
            >
              {traceId}
            </a>
          ) : (
            (traceId ?? "Not recorded")
          )}
        </Row>
      </dl>
    </div>
  );
}
