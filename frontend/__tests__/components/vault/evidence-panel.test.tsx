import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { EvidencePanel } from "@/components/vault/evidence-panel";
import type { Judged } from "@/lib/vault/judged";
import type { HarnessChecks } from "@/lib/vault/types";

const SCORES = {
  render: 96,
  accessibility: 93,
  visual: 91,
  copy: 88,
  novelty: 90,
  compliance: 97,
};

const JUDGED: Judged = {
  scores: SCORES,
  verdict: "published",
  rubricVersion: "seed-v0",
  model: "gpt-6-luna",
  traceId: null,
  checks: null,
};

/** What the sandbox found on an attempt that went through it. */
const FOUND: HarnessChecks = {
  blocked: false,
  passed: 7,
  total: 8,
  checks: [
    { name: "typecheck", ok: true, detail: null },
    { name: "lint", ok: true, detail: null },
    { name: "build", ok: true, detail: null },
    { name: "render", ok: true, detail: null },
    { name: "layout:desktop", ok: true, detail: null },
    { name: "layout:tablet", ok: true, detail: null },
    {
      name: "layout:phone",
      ok: false,
      detail: "The block is 40px wider than a 390px viewport.",
    },
    {
      name: "accessibility",
      ok: false,
      detail: "color-contrast (serious, 2 nodes)",
    },
  ],
  violations: [
    {
      id: "color-contrast",
      impact: "serious",
      help: "Elements must meet minimum colour contrast",
      nodes: 2,
    },
  ],
};

describe("EvidencePanel", () => {
  test("prints every dimension the judge scored", () => {
    render(<EvidencePanel kind="component" judged={JUDGED} />);

    for (const label of [
      "Render",
      "Accessibility",
      "Visual",
      "Copy",
      "Novelty",
      "Compliance",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }

    expect(screen.getByText("PASS")).toBeInTheDocument();
    expect(screen.getByText("gpt-6-luna · seed-v0")).toBeInTheDocument();
  });

  test("can leave the verdict out where everything has already passed", () => {
    render(
      <EvidencePanel kind="component" judged={JUDGED} showVerdict={false} />,
    );

    // The library only holds what cleared its bar, so a stamp there would read
    // PASS on every row; the task page keeps it, because a run can be a refusal.
    expect(screen.queryByText("PASS")).toBeNull();
    expect(screen.getByText("gpt-6-luna · seed-v0")).toBeInTheDocument();
  });

  test("says so when no trace was recorded", () => {
    render(<EvidencePanel kind="component" judged={JUDGED} />);

    expect(screen.getByText("Not recorded")).toBeInTheDocument();
  });

  test("says when no model ran, rather than calling it unknown", () => {
    render(
      <EvidencePanel kind="component" judged={{ ...JUDGED, model: null }} />,
    );

    expect(screen.getByText(/No model ran/)).toBeInTheDocument();
  });

  test("says a run has not been judged yet", () => {
    render(
      <EvidencePanel
        kind="component"
        judged={{
          scores: null,
          verdict: "candidate",
          rubricVersion: null,
          model: null,
          traceId: null,
          checks: null,
        }}
      />,
    );

    expect(screen.getByText("Not judged")).toBeInTheDocument();
    expect(screen.getByText(/No scores yet/)).toBeInTheDocument();
  });

  test("shows an image's three dimensions and none of the block's", () => {
    render(
      <EvidencePanel
        kind="image"
        judged={{
          ...JUDGED,
          scores: { visual: 88, prompt_fit: 91, compliance: 100 },
        }}
      />,
    );

    expect(screen.getByText("Prompt fit")).toBeInTheDocument();
    expect(screen.queryByText("Novelty")).not.toBeInTheDocument();
  });

  test("reads the sandbox's checks, one per thing it looked at", () => {
    // No scores here: "Accessibility" is both a rubric dimension and a check,
    // and this test is about the second.
    render(
      <EvidencePanel
        kind="component"
        judged={{ ...JUDGED, scores: null, checks: FOUND }}
      />,
    );

    expect(screen.getByText("Harness")).toBeInTheDocument();
    expect(screen.getByText("Types")).toBeInTheDocument();
    expect(screen.getByText("Build")).toBeInTheDocument();
    // A layout check is named after its viewport.
    expect(screen.getByText("Phone")).toBeInTheDocument();
    expect(screen.getByText("Accessibility")).toBeInTheDocument();

    // Six passed, and the two that did not say so in the sandbox's words.
    expect(screen.getAllByText("ok")).toHaveLength(6);
    expect(screen.getAllByText("failed")).toHaveLength(2);
    expect(
      screen.getByText(/The block is 40px wider than a 390px viewport/),
    ).toBeInTheDocument();
  });

  test("lists the accessibility findings axe reported", () => {
    render(
      <EvidencePanel
        kind="component"
        judged={{ ...JUDGED, scores: null, checks: FOUND }}
      />,
    );

    expect(screen.getByText("color-contrast")).toBeInTheDocument();
    expect(screen.getByText(/serious · 2 nodes/)).toBeInTheDocument();
  });

  test("says nothing about a harness an artifact never went through", () => {
    render(<EvidencePanel kind="image" judged={JUDGED} />);

    expect(screen.queryByText("Harness")).not.toBeInTheDocument();
  });
});
