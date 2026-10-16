import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { TaskChecklist } from "@/components/vault/task-checklist";
import type { TaskStep } from "@/lib/vault/types";

function step(overrides: Partial<TaskStep>): TaskStep {
  return {
    id: overrides.id ?? "step",
    index: 0,
    name: "A step",
    status: "pending",
    detail: null,
    started_at: null,
    finished_at: null,
    ...overrides,
  };
}

const STEPS: TaskStep[] = [
  step({
    id: "one",
    index: 0,
    name: "Moderating the brief",
    status: "succeeded",
    started_at: "2026-10-14T09:00:00Z",
    finished_at: "2026-10-14T09:00:12Z",
  }),
  step({
    id: "two",
    index: 1,
    name: "Generating the block",
    status: "running",
    detail: { attempts: 2 },
    started_at: "2026-10-14T09:00:12Z",
  }),
  step({ id: "three", index: 2, name: "Judging the attempt" }),
];

describe("TaskChecklist", () => {
  test("keeps the steps in the order the worker wrote them", () => {
    render(<TaskChecklist steps={STEPS} />);

    const rows = screen.getAllByRole("row").slice(1);

    expect(rows.map((row) => row.textContent)).toEqual([
      expect.stringContaining("Moderating the brief"),
      expect.stringContaining("Generating the block"),
      expect.stringContaining("Judging the attempt"),
    ]);
  });

  test("labels each state in words", () => {
    render(<TaskChecklist steps={STEPS} />);

    expect(screen.getByText("Done")).toBeInTheDocument();
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  test("shows the step's own detail under its name", () => {
    render(<TaskChecklist steps={STEPS} />);

    expect(screen.getByText("attempts 2")).toBeInTheDocument();
  });

  test("gives a step that has not finished no duration", () => {
    render(<TaskChecklist steps={STEPS} />);

    expect(screen.getByText("12s")).toBeInTheDocument();
    expect(screen.getAllByText("—")).toHaveLength(2);
  });

  test("reserves the animated caret for the step that is running", () => {
    const { container } = render(<TaskChecklist steps={STEPS} />);

    expect(container.querySelectorAll(".animate-caret")).toHaveLength(1);
  });
});
