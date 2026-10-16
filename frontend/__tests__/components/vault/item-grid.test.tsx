import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { ComponentCell } from "@/components/vault/item-grid";
import type { ComponentSummary } from "@/lib/vault/types";

const COMPONENT: ComponentSummary = {
  id: "0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
  slug: "proof-sheet-hero",
  title: "Proof-sheet hero",
  description: "A left-aligned headline on a rule grid.",
  category_id: "category",
  created_at: "2026-10-14T09:12:00Z",
};

describe("ComponentCell", () => {
  test("files the block under its mark, its type and its date", () => {
    render(
      <ComponentCell
        component={COMPONENT}
        typeName="Hero"
        position={7}
        href="/?item=0199f1ab"
      />,
    );

    expect(screen.getByText("№ 007")).toBeInTheDocument();
    expect(screen.getByText("Hero")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Proof-sheet hero" }),
    ).toBeInTheDocument();
    expect(screen.getByText("14 Oct 2026")).toBeInTheDocument();
    expect(screen.getByText("proof-sheet-hero")).toBeInTheDocument();
  });

  test("the whole cell is the way into the item", () => {
    render(
      <ComponentCell
        component={COMPONENT}
        typeName="Hero"
        position={1}
        href="/?item=0199f1ab"
      />,
    );

    expect(screen.getByRole("link")).toHaveAttribute("href", "/?item=0199f1ab");
  });
});
