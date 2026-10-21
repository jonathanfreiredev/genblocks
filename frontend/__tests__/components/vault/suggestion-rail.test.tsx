import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { SuggestionRail } from "@/components/vault/suggestion-rail";
import type { Suggestion } from "@/lib/vault/types";

const BLOCK: Suggestion = {
  kind: "component",
  id: "0b9c1e2a-aaaa-bbbb-cccc-ddddeeeeffff",
  title: "Tiered pricing",
  detail: "Three plans in a ruled table",
  path: "genblocks/screenshots/abc-1",
  width: null,
  height: null,
};

const PICTURE: Suggestion = {
  kind: "image",
  id: "0b9c1e2a-9999-8888-7777-666655554444",
  title: "A coastal path at dawn",
  detail: "960×640",
  path: "genblocks/images/xyz",
  width: 960,
  height: 640,
};

describe("SuggestionRail", () => {
  test("shows one card per thing the agent found", () => {
    render(<SuggestionRail items={[BLOCK, PICTURE]} />);

    expect(screen.getByText("Tiered pricing")).toBeInTheDocument();
    expect(screen.getByText("A coastal path at dawn")).toBeInTheDocument();
    expect(screen.getAllByRole("link")).toHaveLength(2);
  });

  test("each card opens the item it shows", () => {
    render(<SuggestionRail items={[BLOCK]} />);

    // The gallery's own URL: the item dialog is a query parameter there, so a
    // card is a link and the browser can keep it.
    expect(
      screen.getByRole("link", { name: /Tiered pricing/ }),
    ).toHaveAttribute("href", `/blocks/${BLOCK.id}`);
  });

  test("names the kind of each card in words", () => {
    render(<SuggestionRail items={[BLOCK, PICTURE]} />);

    expect(screen.getByText("Block")).toBeInTheDocument();
    expect(screen.getByText("Image")).toBeInTheDocument();
  });

  test("an image card opens the image page", () => {
    render(<SuggestionRail items={[PICTURE]} />);

    expect(
      screen.getByRole("link", { name: /A coastal path at dawn/ }),
    ).toHaveAttribute("href", `/images/${PICTURE.id}`);
  });

  test("gives a block with no render something to show rather than an empty frame", () => {
    render(<SuggestionRail items={[{ ...BLOCK, path: null }]} />);

    // A seeded block predates renders. The frame says why it is empty, rather
    // than repeating the kind the label below already gives.
    expect(screen.queryByRole("img")).toBeNull();
    expect(screen.getByText("No render yet")).toBeInTheDocument();
  });

  test("draws nothing when there is nothing to show", () => {
    const { container } = render(<SuggestionRail items={[]} />);

    expect(container).toBeEmptyDOMElement();
  });
});
