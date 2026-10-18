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
  winning_generation_id: "second",
  created_by: null,
  license: "MIT",
};

function attempt(overrides: Partial<Generation>): Generation {
  return {
    id: "attempt",
    task_id: "task",
    component_id: "component",
    attempt_no: 1,
    code: "export default function Block() { return null }",
    files: null,
    screenshot_path: null,
    checks: null,
    scores: null,
    verdict: "published",
    rubric_version: "canned-v1",
    model: "gpt-6-luna",
    langfuse_trace_id: null,
    created_at: "2026-10-17T09:12:00Z",
    ...overrides,
  };
}

const GENERATIONS = [
  attempt({ id: "first", attempt_no: 1, screenshot_path: null }),
  attempt({
    id: "second",
    attempt_no: 2,
    screenshot_path: "genblocks/screenshots/0123456789ab-2",
  }),
];

describe("ComponentDialog", () => {
  test("shows the render of the attempt the ledger has selected", () => {
    render(
      <ComponentDialog
        component={COMPONENT}
        generations={GENERATIONS}
        typeName="Hero"
        closeHref="/"
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Render" }));

    // The winning attempt is the one selected, and it has a render: the plate
    // carries the block's name, and the caption names what made it.
    expect(screen.getByText(/Attempt № 2 of 2/)).toBeInTheDocument();
    expect(
      screen.getByAltText("The rendered block: Newsletter band"),
    ).toBeInTheDocument();
  });

  test("says an attempt has no render rather than drawing an empty frame", () => {
    render(
      <ComponentDialog
        component={COMPONENT}
        generations={[GENERATIONS[0]]}
        typeName="Hero"
        closeHref="/"
      />,
    );

    fireEvent.click(screen.getByRole("tab", { name: "Render" }));

    expect(screen.getByText("Awaiting asset")).toBeInTheDocument();
    expect(
      screen.getByText("No render was taken for this attempt."),
    ).toBeInTheDocument();
  });

  test("keeps the code as the specimen it opens on", () => {
    render(
      <ComponentDialog
        component={COMPONENT}
        generations={GENERATIONS}
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
        generations={GENERATIONS}
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
        generations={GENERATIONS}
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
        generations={GENERATIONS}
        typeName="Hero"
        closeHref="/"
      />,
    );

    expect(screen.queryByText(/pnpm add/)).toBeNull();
  });
});
