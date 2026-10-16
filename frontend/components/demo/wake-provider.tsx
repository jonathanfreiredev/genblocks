"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { probeDemoServices, sleep } from "@/lib/demo-wake";

/**
 * What the page knows about the demo's services.
 *
 * `unknown` is the honest starting point: nothing has been asked yet. `ready` is what
 * the answer becomes when they turn out to be up, and it is deliberately silent — a
 * page has nothing to say about services that were never down.
 */
export type DemoWakeState = "unknown" | "waking" | "ready" | "unreachable";

type DemoWake = {
  state: DemoWakeState;
  /** Ask again now. For a page that just found the services asleep after all. */
  check: () => void;
  /** Say what a page saw first-hand, when it learns it sooner than the polling does. */
  note: (seen: DemoWakeState) => void;
};

/**
 * Components rendered outside the provider — a test, or a page that forgot one — are
 * told that nothing is known, which is what makes them behave as they would with no
 * wake-up logic at all.
 */
const DemoWakeContext = createContext<DemoWake>({
  state: "unknown",
  check: () => {},
  note: () => {},
});

/** How long to leave between two questions while the services are coming up. */
const POLL_INTERVAL_MS = 3_000;

/**
 * How long a visitor is asked to wait before the page stops saying the demo is waking
 * and starts saying it did not come up. Generous on purpose: the API has to answer
 * before it can wake the MCP, so two cold containers start one after the other — and
 * the visitor is reading the page meanwhile.
 */
const WAKE_BUDGET_MS = 120_000;

/**
 * Keeps the demo's services awake while somebody is on the site.
 *
 * Mounted once, around every page, because the pages that need the services are the
 * landing, the playground and the sign-in pages, and all of them sit under it. It asks
 * as soon as it mounts, which is what turns "the first visit of the day is slow" into a
 * wait the visitor spends reading rather than one they spend staring at a button.
 */
export function DemoWakeProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<DemoWakeState>("unknown");
  // Bumped by `check`, which is what asks the effect below for another round.
  const [round, setRound] = useState(0);

  const check = useCallback(() => setRound((turns) => turns + 1), []);
  const note = useCallback((seen: DemoWakeState) => setState(seen), []);

  useEffect(() => {
    let stopped = false;
    const deadline = Date.now() + WAKE_BUDGET_MS;

    async function keepAsking() {
      while (!stopped) {
        // A hidden tab is nobody waiting. Asking anyway would keep two containers awake
        // for an audience of none, which is the cost this whole arrangement exists to
        // avoid.
        if (!document.hidden) {
          if ((await probeDemoServices()) === "ready") {
            if (!stopped) setState("ready");
            return;
          }

          if (stopped) return;

          if (Date.now() >= deadline) {
            setState("unreachable");
            return;
          }

          setState("waking");
        }

        await sleep(POLL_INTERVAL_MS);
      }
    }

    void keepAsking();

    return () => {
      stopped = true;
    };
  }, [round]);

  return (
    <DemoWakeContext.Provider value={{ state, check, note }}>
      {children}
    </DemoWakeContext.Provider>
  );
}

/** What the demo's services are doing, as far as the nearest provider can tell. */
export function useDemoWake(): DemoWake {
  return useContext(DemoWakeContext);
}
