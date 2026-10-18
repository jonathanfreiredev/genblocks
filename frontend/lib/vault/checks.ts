import type { HarnessChecks } from "@/lib/vault/types";

/**
 * What each check the sandbox makes is called on the evidence panel.
 *
 * The names are the sandbox's (``app/harness/schemas.py``); the labels are
 * shorter because a reader learns them once. A check nobody has heard of is
 * shown under its own name: one added later should appear, not vanish.
 */
const LABELS: Record<string, string> = {
  typecheck: "Types",
  lint: "Lint",
  build: "Build",
  render: "Render",
  accessibility: "Accessibility",
};

// A layout check is one per viewport: ``layout:desktop`` and so on.
const LAYOUT_PREFIX = "layout:";

export interface CheckRow {
  label: string;
  ok: boolean;
  /** The sandbox's own words when something failed, and nothing when it did not. */
  detail: string | null;
}

/** One row per check, in the order the sandbox made them. */
export function checkRows(checks: HarnessChecks | null): CheckRow[] {
  if (!checks) {
    return [];
  }

  return checks.checks.map((check) => ({
    label: labelFor(check.name),
    ok: check.ok,
    detail: check.detail,
  }));
}

/** How one check's name reads. */
export function labelFor(name: string): string {
  if (name.startsWith(LAYOUT_PREFIX)) {
    const viewport = name.slice(LAYOUT_PREFIX.length);

    return viewport.charAt(0).toUpperCase() + viewport.slice(1);
  }

  return LABELS[name] ?? name;
}
