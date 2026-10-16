import { act, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { WakeNotice } from "@/components/demo/wake-notice";
import { DemoWakeProvider } from "@/components/demo/wake-provider";

const { probe } = vi.hoisted(() => ({ probe: vi.fn() }));

// The provider's one door to the outside. Replaced so a test can decide what the
// services answer without a network in the middle.
vi.mock("@/lib/demo-wake", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/lib/demo-wake")>()),
  probeDemoServices: probe,
}));

function Wake() {
  return (
    <DemoWakeProvider>
      <WakeNotice />
    </DemoWakeProvider>
  );
}

afterEach(() => {
  probe.mockReset();
  vi.useRealTimers();
});

describe("WakeNotice", () => {
  test("says nothing to a visitor who arrives while the demo is up", async () => {
    probe.mockResolvedValue("ready");

    render(<Wake />);

    // It did ask — that question is the whole point of the provider — and the answer
    // was that there is nothing worth saying.
    await waitFor(() => expect(probe).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole("status")).toBeNull();
  });

  test("tells the visitor the demo is waking", async () => {
    probe.mockResolvedValue("waking");

    render(<Wake />);

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Waking the demo",
    );
  });

  test("stops promising a wake-up once the wait is spent", async () => {
    // Date is faked along with the timers: the budget the provider gives the services
    // is wall-clock, not a number of rounds.
    vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout", "Date"] });
    probe.mockResolvedValue("waking");

    render(<Wake />);

    await act(async () => {});
    expect(screen.getByRole("status")).toHaveTextContent("Waking the demo");

    // The budget the provider gives the services before it stops expecting them.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(120_000);
    });

    expect(screen.getByRole("status")).toHaveTextContent(
      "The demo is still asleep",
    );
    expect(probe).toHaveBeenCalled();
  });
});
