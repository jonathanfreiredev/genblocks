import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { ConnectAgent } from "@/components/mcp/connect-agent";

const ENDPOINT = "http://localhost:8001/mcp";

describe("ConnectAgent", () => {
  test("states the endpoint and the mode it was resolved in", () => {
    render(<ConnectAgent endpoint={ENDPOINT} mode="local" />);

    expect(screen.getAllByText(ENDPOINT).length).toBeGreaterThan(0);
    expect(screen.getByText("Local")).toBeInTheDocument();
    expect(
      screen.getByText(/development server on port 8001/),
    ).toBeInTheDocument();
  });

  test("names every client it documents", () => {
    render(<ConnectAgent endpoint={ENDPOINT} mode="production" />);

    for (const name of ["opencode", "Claude Code", "Cursor", "n8n"]) {
      expect(screen.getByText(name)).toBeInTheDocument();
    }
  });

  test("shows the first client's command before anything is clicked", () => {
    render(<ConnectAgent endpoint={ENDPOINT} mode="production" />);

    expect(
      screen.getByText(`opencode mcp add genblocks --global --url ${ENDPOINT}`),
    ).toBeInTheDocument();
  });

  test("says the commands point at the published server", () => {
    render(<ConnectAgent endpoint={ENDPOINT} mode="production" />);

    expect(screen.getByText("Production")).toBeInTheDocument();
    expect(screen.getByText(/published address/)).toBeInTheDocument();
  });

  test("links to the consent step and the profile that can revoke it", () => {
    render(<ConnectAgent endpoint={ENDPOINT} mode="local" />);

    expect(
      screen.getByRole("link", { name: /Connected applications/ }),
    ).toHaveAttribute("href", "/profile");
  });
});
