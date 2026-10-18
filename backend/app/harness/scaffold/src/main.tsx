import { StrictMode, type ComponentType } from "react";
import { createRoot } from "react-dom/client";

import * as block from "./Block";
import "./index.css";

/**
 * The one place a generated block is mounted.
 *
 * The block's own file is written by the sandbox on every run and replaces
 * whatever was here before: `src/Block.tsx` in this repository is a sample, so
 * the scaffold can be built and iterated on by hand.
 */
const exported = block as unknown as Record<string, unknown>;

/**
 * The block the generator exported: its default if it has one, otherwise the
 * first export named like a component.
 *
 * A named export is accepted on purpose. The prompt asks for a default, and
 * failing a run over a naming choice would be the scaffold inventing a rule the
 * product does not have.
 */
function pickBlock(): ComponentType | undefined {
  const named = Object.entries(exported).find(
    ([name, value]) => typeof value === "function" && /^[A-Z]/.test(name),
  );

  return (exported.default ?? named?.[1]) as ComponentType | undefined;
}

const Block = pickBlock();

if (!Block) {
  throw new Error("The block module exports no component.");
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {/* The page provides the landmark the block lives in. Without it, axe's
        landmark rules would report the scaffold's page rather than the block,
        and the judge would be reading findings nobody wrote. */}
    <main>
      <Block />
    </main>
  </StrictMode>,
);
