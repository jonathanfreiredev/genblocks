import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

import { ComponentDialog } from "@/components/vault/item-dialog";
import type { Component, Generation } from "@/lib/vault/types";

const COMPONENT: Component = {
  id: "component",
  slug: "newsletter-band-1a2b",
  title: "Newsletter band",
  description: "A signup band for a changelog.",
  category_id: "hero",
  created_at: "2026-10-17T09:12:00Z",
  files: { "src/Block.tsx": "export default function Block() { return null }" },
  entry: "src/Block.tsx",
  dependencies: null,
  delivery_prompt: "A newsletter band",
  spec: null,
  winning_generation_id: "run",
  created_by: null,
  license: "MIT",
};

/** The one artifact a task produces, as the panel and the panes read it. */
function run(overrides: Partial<Generation>): Generation {
  return {
    id: "run",
    task_id: "task",
    component_id: "component",
    attempt_no: 1,
    files: {
      "src/Block.tsx": "export default function Block() { return null }",
    },
    entry: "src/Block.tsx",
    screenshot_path: null,
    checks: null,
    scores: null,
    verdict: "published",
    rubric_version: "components-1a2b3c4d",
    model: "gpt-6-luna",
    langfuse_trace_id: null,
    created_at: "2026-10-17T09:12:00Z",
    ...overrides,
  };
}

const RENDERED = [
  run({
    screenshot_path: "genblocks/screenshots/0123456789ab-1",
    scores: {
      render: 92,
      accessibility: 88,
      visual: 86,
      copy: 90,
      compliance: 94,
    },
  }),
];

function open(generations: Generation[] = RENDERED, component = COMPONENT) {
  render(
    <ComponentDialog
      component={component}
      generations={generations}
      typeName="Hero"
      closeHref="/"
    />,
  );
}

describe("ComponentDialog", () => {
  test("opens on the render, with the scores already beside it", () => {
    open();

    // Somebody browsing came to see the block; the numbers are there without a
    // second click, and the code is one tab away.
    expect(
      screen.getByAltText("The rendered block: Newsletter band"),
    ).toBeInTheDocument();
    expect(screen.getByText("Judge")).toBeInTheDocument();
    expect(screen.getByText("94")).toBeInTheDocument();
  });

  test("does not stamp PASS on an item that is in the library", () => {
    open();

    // Everything here has already cleared its bar; the item being on show is the
    // verdict, and the stamp would be the same word on every row.
    expect(screen.queryByText("PASS")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Hide the scores" }),
    ).toBeInTheDocument();
  });

  test("names what made the run and which rubric scored it", () => {
    open();

    expect(
      screen.getByText("gpt-6-luna · components-1a2b3c4d"),
    ).toBeInTheDocument();
  });

  test("says a run has no render rather than drawing an empty frame", () => {
    open([run({})]);

    expect(screen.getByText("Awaiting asset")).toBeInTheDocument();
    expect(
      screen.getByText("No render was taken for this run."),
    ).toBeInTheDocument();
  });

  test("reads the code one file at a time, once the tab is opened", () => {
    // The project the pane reads is the run's: the component's copy is the same
    // project, and the run is where it came from.
    const project = {
      "src/Block.tsx": "export default function Block() { return <Rule /> }",
      "src/parts/Rule.tsx": "export default function Rule() { return <hr /> }",
    };

    open([run({ files: project })]);

    // Not on screen until asked for: the render is what the dialog opens on.
    expect(screen.queryByText(/function Rule/)).toBeNull();

    fireEvent.click(screen.getByRole("tab", { name: "Code" }));

    // Both files are named, and the entry point is the one on screen: it is the
    // file the page imports, so it is the one a reader opens first.
    expect(
      screen.getByRole("button", { name: "src/Block.tsx" }),
    ).toHaveAttribute("aria-pressed", "true");

    fireEvent.click(screen.getByRole("button", { name: "src/parts/Rule.tsx" }));

    expect(screen.getByText(/function Rule/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "src/parts/Rule.tsx" }),
    ).toHaveAttribute("aria-pressed", "true");
  });

  test("opens the file the block names, not the alphabetically first one", () => {
    // `src/App.tsx` sorts before `src/Block.tsx`; the block is `Block`, and the
    // entry is what says so. Without it the pane would open the wrong file.
    const project = {
      "src/App.tsx": "export default function App() { return null }",
      "src/Block.tsx": "export default function Block() { return <main /> }",
    };

    open([run({ files: project, entry: "src/Block.tsx" })]);
    fireEvent.click(screen.getByRole("tab", { name: "Code" }));

    expect(
      screen.getByRole("button", { name: "src/Block.tsx" }),
    ).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByText(/function Block/)).toBeInTheDocument();
  });

  test("says what to install beside a block, and nothing when there is nothing", () => {
    const block = {
      ...COMPONENT,
      dependencies: {
        react: "^19.2.4",
        "react-dom": "^19.2.4",
        motion: "^13.0.0",
      },
    };

    open(RENDERED, block);
    fireEvent.click(screen.getByRole("tab", { name: "Code" }));

    expect(screen.getByText(/pnpm add motion@\^13\.0\.0/)).toBeInTheDocument();
    // React is what a block is written in, not something it asks anyone to add.
    expect(screen.queryByText(/react@/)).toBeNull();
  });

  test("has no install line when the block adds nothing", () => {
    open();
    fireEvent.click(screen.getByRole("tab", { name: "Code" }));

    expect(screen.queryByText(/pnpm add/)).toBeNull();
  });

  test("puts the scores away and brings them back from the same spot", () => {
    open();

    fireEvent.click(screen.getByRole("button", { name: "Hide the scores" }));

    expect(screen.queryByText("Judge")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Show the scores" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Show the scores" }));

    expect(screen.getByText("Judge")).toBeInTheDocument();
  });

  test("puts the files away without putting the code away", () => {
    const project = {
      "src/Block.tsx": "export default function Block() { return null }",
      "src/parts/Rule.tsx": "export default function Rule() { return <hr /> }",
    };

    open([run({ files: project })]);
    fireEvent.click(screen.getByRole("tab", { name: "Code" }));

    fireEvent.click(screen.getByRole("button", { name: "Hide the files" }));

    expect(
      screen.queryByRole("button", { name: "src/parts/Rule.tsx" }),
    ).toBeNull();
    expect(screen.getByText(/function Block/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Show the files" }),
    ).toBeInTheDocument();
  });
});
