import type { Generation, HarnessChecks, Verdict } from "@/lib/vault/types";

/** What one judged artifact says about itself. */
export interface Judged {
  scores: Record<string, number> | null;
  verdict: Verdict;
  rubricVersion: string | null;
  model: string | null;
  traceId: string | null;
  /** What the sandbox found, when the artifact came out of one. */
  checks: HarnessChecks | null;
}

/**
 * What a run says about itself, ready for the evidence panel.
 *
 * In a plain module rather than beside the panel because both the item dialog and
 * the task page build one, and the task page is a server component: a function
 * exported from a client module cannot be called there.
 *
 * A generated task produces one artifact, so this takes the one there is, and a
 * run that never got as far as being judged reads as an unjudged panel rather
 * than a blank: "no scores yet" is a fact about the run.
 */
export function judgedFrom(generation: Generation | null): Judged {
  return {
    scores: generation?.scores ?? null,
    verdict: generation?.verdict ?? "candidate",
    rubricVersion: generation?.rubric_version ?? null,
    model: generation?.model ?? null,
    traceId: generation?.langfuse_trace_id ?? null,
    checks: generation?.checks ?? null,
  };
}
