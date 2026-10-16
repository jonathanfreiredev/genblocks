import type { Kind, Verdict } from "@/lib/vault/types";

/**
 * The two rubrics, as the judge writes them.
 *
 * The keys are the contract between the judge and the panel; the labels live
 * here so no view invents its own wording for a dimension.
 */
const COMPONENT_RUBRIC = [
  { key: "render", label: "Render" },
  { key: "accessibility", label: "Accessibility" },
  { key: "visual", label: "Visual" },
  { key: "copy", label: "Copy" },
  { key: "novelty", label: "Novelty" },
  { key: "compliance", label: "Compliance" },
] as const;

const IMAGE_RUBRIC = [
  { key: "visual", label: "Visual quality" },
  { key: "prompt_fit", label: "Prompt fit" },
  { key: "compliance", label: "Compliance" },
] as const;

export interface Dimension {
  key: string;
  label: string;
}

export interface ScoredDimension {
  dimension: Dimension;
  value: number;
}

export function rubricFor(kind: Kind): readonly Dimension[] {
  return kind === "image" ? IMAGE_RUBRIC : COMPONENT_RUBRIC;
}

/** The rubric's rows paired with what the judge wrote for them, in rubric order. */
export function scoresFor(
  kind: Kind,
  scores: Record<string, number> | null,
): ScoredDimension[] {
  if (!scores) {
    return [];
  }

  return rubricFor(kind)
    .filter((dimension) => typeof scores[dimension.key] === "number")
    .map((dimension) => ({ dimension, value: scores[dimension.key] }));
}

/**
 * The dimension that decided the verdict.
 *
 * Every dimension has its own threshold, so the mean hides the number that
 * mattered; the weakest one is what the ledger row is worth reading.
 */
export function weakestDimension(
  scores: Record<string, number> | null,
): ScoredDimension | null {
  if (!scores) {
    return null;
  }

  const entries = [...COMPONENT_RUBRIC, ...IMAGE_RUBRIC].filter(
    (dimension) => typeof scores[dimension.key] === "number",
  );

  if (entries.length === 0) {
    return null;
  }

  const lowest = entries.reduce((worst, dimension) =>
    scores[dimension.key] < scores[worst.key] ? dimension : worst,
  );

  return { dimension: lowest, value: scores[lowest.key] };
}

/** The stamp a verdict wears; `null` while nobody has judged the attempt. */
const STAMPS: Record<Verdict, "pass" | "retry" | "fail" | null> = {
  published: "pass",
  rejected: "fail",
  candidate: null,
};

export function stampFor(verdict: Verdict): "pass" | "retry" | "fail" | null {
  return STAMPS[verdict];
}
