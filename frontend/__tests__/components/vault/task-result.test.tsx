import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { TaskResult } from "@/components/vault/task-result";
import type { Generation } from "@/lib/vault/types";

function run(overrides: Partial<Generation>): Generation {
  return {
    id: "run",
    task_id: "task",
    component_id: null,
    attempt_no: 1,
    code: "export default function Block() { return null }",
    files: null,
    screenshot_path: null,
    checks: null,
    scores: null,
    verdict: "candidate",
    rubric_version: null,
    model: "gpt-6-luna",
    langfuse_trace_id: null,
    created_at: "2026-10-18T09:12:00Z",
    ...overrides,
  };
}

const SCORED = run({
  screenshot_path: "genblocks/screenshots/0123456789ab-1",
  verdict: "rejected",
  rubric_version: "components-1a2b3c4d",
  scores: {
    render: 92,
    accessibility: 88,
    visual: 61,
    copy: 74,
    compliance: 90,
  },
});

describe("TaskResult", () => {
  test("shows the render the run left, named by the brief", () => {
    render(<TaskResult generation={SCORED} brief="A pricing table" />);

    expect(
      screen.getByAltText("The block this task produced: A pricing table"),
    ).toBeInTheDocument();
    expect(screen.queryByText("No render was taken for this run.")).toBeNull();
  });

  test("says a run has no render rather than drawing an empty frame", () => {
    render(<TaskResult generation={run({})} brief="A pricing table" />);

    expect(
      screen.getByText("No render was taken for this run."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("img")).toBeNull();
  });

  test("carries the numbers the judge gave the run, verdict included", () => {
    render(<TaskResult generation={SCORED} brief="A pricing table" />);

    // The refusal is legible on the task even though nothing was published:
    // that is the whole reason a failed run keeps its artifact.
    expect(screen.getByText("REJECTED")).toBeInTheDocument();
    expect(screen.getByText("Visual")).toBeInTheDocument();
    expect(screen.getByText("61")).toBeInTheDocument();
    expect(
      screen.getByText("gpt-6-luna · components-1a2b3c4d"),
    ).toBeInTheDocument();
  });

  test("says nobody has judged it when the run never reached the judge", () => {
    render(<TaskResult generation={run({})} brief="A pricing table" />);

    expect(screen.getByText("Not judged")).toBeInTheDocument();
    expect(screen.getByText(/No scores yet/)).toBeInTheDocument();
  });
});
