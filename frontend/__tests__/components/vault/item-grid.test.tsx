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
  author: "Marisol Vega",
  screenshot_path: "genblocks/screenshots/proof-sheet-hero",
};

describe("ComponentCell", () => {
  test("is a picture and the maker, and nothing else", () => {
    render(
      <ComponentCell
        component={COMPONENT}
        href="/blocks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b"
      />,
    );

    expect(
      screen.getByRole("link", { name: "Proof-sheet hero" }),
    ).toHaveAttribute("href", "/blocks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b");
    expect(screen.getByText("Marisol Vega")).toBeInTheDocument();
    // The wall carries no titles, slugs or dates: the picture is the label.
    expect(screen.queryByText("proof-sheet-hero")).not.toBeInTheDocument();
    expect(screen.queryByText("14 Oct 2026")).not.toBeInTheDocument();
  });

  test("calls an unclaimed block the house's", () => {
    render(
      <ComponentCell
        component={{ ...COMPONENT, author: null }}
        href="/blocks/0199f1ab"
      />,
    );

    expect(screen.getByText("GenBlocks")).toBeInTheDocument();
  });

  test("falls back to the title when there is no render", () => {
    render(
      <ComponentCell
        component={{ ...COMPONENT, screenshot_path: null }}
        href="/blocks/0199f1ab"
      />,
    );

    expect(screen.getByText("Proof-sheet hero")).toBeInTheDocument();
  });
});
