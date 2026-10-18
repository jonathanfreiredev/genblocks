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
  code: "export default function Block() { return null }",
  files: null,
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
    code: "export default function Block() { return null }",
    files: null,
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
  run({ screenshot_path: "genblocks/screenshots/0123456789ab-1" }),
];

describe("ComponentDialog", () => {
  test("shows the render of the run that made it", () => {
    render(
      <ComponentDialog
        component={COMPONENT}
        generations={RENDERED}
        typeName="Hero"
        closeHref="/"
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Render" }));

    // The plate carries the block's name, and the panel beside it names what made
    // the run and which rubric scored it.
    expect(
      screen.getByAltText("The rendered block: Newsletter band"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("gpt-6-luna · components-1a2b3c4d"),
    ).toBeInTheDocument();
  });

  test("says a run has no render rather than drawing an empty frame", () => {
    render(
      <ComponentDialog
        component={COMPONENT}
        generations={[run({})]}
        typeName="Hero"
        closeHref="/"
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Render" }));

    expect(screen.getByText("Awaiting asset")).toBeInTheDocument();
    expect(
      screen.getByText("No render was taken for this run."),
    ).toBeInTheDocument();
  });

  test("keeps the code as the specimen it opens on", () => {
    render(
      <ComponentDialog
        component={COMPONENT}
        generations={RENDERED}
        typeName="Hero"
        closeHref="/"
      />,
    );

    expect(screen.getByRole("tab", { name: "Code" })).toBeInTheDocument();
    expect(
      screen.getByRole("tab", { name: "Delivery prompt" }),
    ).toBeInTheDocument();
    expect(screen.getByText(COMPONENT.code)).toBeInTheDocument();
  });

  test("reads a block that is several files, one file at a time", () => {
    const block = {
      ...COMPONENT,
      code: "export default function Block() { return <Rule /> }",
      files: {
        "src/Block.tsx": "export default function Block() { return <Rule /> }",
        "src/parts/Rule.tsx":
          "export default function Rule() { return <hr /> }",
      },
    };

    render(
      <ComponentDialog
        component={block}
        generations={RENDERED}
        typeName="Hero"
        closeHref="/"
      />,
    );

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

  test("says what to install beside a block, and nothing when there is nothing", () => {
    const block = {
      ...COMPONENT,
      dependencies: {
        react: "^19.2.4",
        "react-dom": "^19.2.4",
        motion: "^13.0.0",
      },
    };

    const { unmount } = render(
      <ComponentDialog
        component={block}
        generations={RENDERED}
        typeName="Hero"
        closeHref="/"
      />,
    );

    expect(screen.getByText(/pnpm add motion@\^13\.0\.0/)).toBeInTheDocument();
    // React is what a block is written in, not something it asks anyone to add.
    expect(screen.queryByText(/react@/)).toBeNull();

    unmount();

    render(
      <ComponentDialog
        component={COMPONENT}
        generations={RENDERED}
        typeName="Hero"
        closeHref="/"
      />,
    );

    expect(screen.queryByText(/pnpm add/)).toBeNull();
  });
});
