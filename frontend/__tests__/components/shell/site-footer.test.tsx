import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { SiteFooter } from "@/components/shell/site-footer";

describe("SiteFooter", () => {
  test("links to About and the legal notices", () => {
    render(<SiteFooter />);

    expect(screen.getByRole("link", { name: "About" })).toHaveAttribute(
      "href",
      "/about",
    );
    expect(screen.getByRole("link", { name: "Impressum" })).toHaveAttribute(
      "href",
      "/impressum",
    );
    expect(screen.getByRole("link", { name: "Privacy" })).toHaveAttribute(
      "href",
      "/privacy",
    );
    expect(screen.getByRole("link", { name: "Terms" })).toHaveAttribute(
      "href",
      "/terms",
    );
    expect(
      screen.queryByRole("link", { name: "Contact" }),
    ).not.toBeInTheDocument();
  });
});
