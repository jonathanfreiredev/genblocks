import type { Attempt } from "@/components/ui/attempt-ledger";
import { formatDate, formatTime } from "@/lib/vault/format";
import { stampFor, weakestDimension } from "@/lib/vault/rubric";
import type { Generation } from "@/lib/vault/types";

/**
 * The attempt history as the ledger reads it, oldest first.
 *
 * The score cell carries the rubric's weakest dimension rather than a mean:
 * every dimension has its own threshold, so a mean can look respectable on an
 * attempt the judge rejected, and that is the one thing this table must never
 * do. An unjudged attempt has no number at all.
 */
export function attemptRows(generations: Generation[]): Attempt[] {
  return generations.map((generation) => {
    const weakest = weakestDimension(generation.scores);

    return {
      attempt: generation.attempt_no,
      timestamp: `${formatDate(generation.created_at)} ${formatTime(generation.created_at)}`,
      score: weakest?.value ?? null,
      scoreNote: weakest?.dimension.label,
      verdict: stampFor(generation.verdict),
    };
  });
}
