import type { Kind, Verdict } from "@/lib/vault/types";

/**
 * The two rubrics, as the judge writes them.
 *
 * The keys are the contract between the judge and the panel; the labels live
 * here so no view invents its own wording for a dimension. `novelty` is kept for
 * seeded legacy attempts: the current component rubric does not emit it, so a new
 * attempt simply has one row fewer.
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
 * The stamp a verdict wears; `null` while nobody has judged the run.
 *
 * A rejection is a failure rather than a "retry": there is no second attempt to
 * offer, so the two states are the two outcomes.
 */
const STAMPS: Record<Verdict, "pass" | "fail" | null> = {
  published: "pass",
  rejected: "fail",
  candidate: null,
};

export function stampFor(verdict: Verdict): "pass" | "fail" | null {
  return STAMPS[verdict];
}
