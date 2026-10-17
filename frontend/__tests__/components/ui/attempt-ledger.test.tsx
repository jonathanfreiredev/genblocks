import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

import { AttemptLedger, type Attempt } from "@/components/ui/attempt-ledger";

const ATTEMPTS: Attempt[] = [
  {
    attempt: 1,
    timestamp: "14 Oct, 09:12",
    score: 33,
    scoreNote: "Novelty",
    verdict: "fail",
  },
  {
    attempt: 2,
    timestamp: "14 Oct, 09:14",
    score: 90,
    scoreNote: "Visual",
    verdict: "pass",
  },
];

describe("AttemptLedger", () => {
  test("walks the history by its numbers when a reader can pick one", () => {
    const onSelectAttempt = vi.fn();

    render(
      <AttemptLedger
        attempts={ATTEMPTS}
        selectedAttempt={2}
        onSelectAttempt={onSelectAttempt}
      />,
    );

    // The control is the number, and it says what it does: a row that is quietly
    // clickable is a row a keyboard and a screen reader cannot find.
    const chosen = screen.getByRole("button", { name: /show attempt 2/ });
    expect(chosen).toHaveAttribute("aria-current", "true");

    fireEvent.click(screen.getByRole("button", { name: /show attempt 1/ }));

    expect(onSelectAttempt).toHaveBeenCalledWith(1);
  });

  test("a history nobody can pick carries no controls", () => {
    render(<AttemptLedger attempts={ATTEMPTS} />);

    expect(screen.queryAllByRole("button")).toHaveLength(0);
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  test("reads each attempt by the dimension that decided it", () => {
    render(<AttemptLedger attempts={ATTEMPTS} scoreHeading="Lowest" />);

    expect(screen.getByText("Lowest")).toBeInTheDocument();
    expect(screen.getByText("33")).toBeInTheDocument();
    expect(screen.getByText("Novelty")).toBeInTheDocument();
    expect(screen.getByText("REJECTED")).toBeInTheDocument();
    expect(screen.getByText("PASS")).toBeInTheDocument();
  });

  test("does not judge an attempt nobody has judged", () => {
    render(
      <AttemptLedger
        attempts={[
          { attempt: 1, timestamp: "today", score: null, verdict: null },
        ]}
      />,
    );

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(screen.getByText("Not judged")).toBeInTheDocument();
  });

  test("passes through the props a table already has", () => {
    render(<AttemptLedger attempts={ATTEMPTS} aria-label="Attempt history" />);

    expect(
      screen.getByRole("table", { name: "Attempt history" }),
    ).toBeInTheDocument();
  });
});
