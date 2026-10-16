import { render, screen } from "@testing-library/react";
import { describe, expect, test } from "vitest";

import { OAuthConsent, OAuthConsentError } from "@/components/oauth-consent";

const PROPS = {
  authorizationId: "auth-123",
  clientName: "Claude Code",
  clientUri: "https://claude.ai",
  redirectUri: "http://localhost:6274/callback",
  scope: "openid email",
};

describe("OAuthConsent", () => {
  test("names the client and translates the scopes", () => {
    render(<OAuthConsent {...PROPS} />);

    expect(screen.getByText(/Authorize Claude Code/)).toBeInTheDocument();
    expect(screen.getByText("Confirm who you are")).toBeInTheDocument();
    expect(screen.getByText("See your email address")).toBeInTheDocument();
  });

  test("says the client will act with the user's own access", () => {
    render(<OAuthConsent {...PROPS} />);

    expect(screen.getByText(/the same access you have/)).toBeInTheDocument();
  });

  test("posts the decision with the authorization id", () => {
    const { container } = render(<OAuthConsent {...PROPS} />);

    const form = container.querySelector("form");
    expect(form).toHaveAttribute("action", "/api/oauth/decision");
    expect(form).toHaveAttribute("method", "post");
    expect(
      container.querySelector('input[name="authorization_id"]'),
    ).toHaveValue(PROPS.authorizationId);

    // A submit button carries the decision as its value.
    const approve = screen.getByRole("button", { name: "Approve" });
    expect(approve).toHaveAttribute("name", "decision");
    expect(approve).toHaveAttribute("value", "approve");
    expect(screen.getByRole("button", { name: "Deny" })).toHaveAttribute(
      "value",
      "deny",
    );
  });

  test("omits the scope list when the client requested nothing", () => {
    render(<OAuthConsent {...PROPS} scope="" />);

    expect(screen.queryByText("It will be able to:")).not.toBeInTheDocument();
  });

  test("warns when the previous decision did not go through", () => {
    render(<OAuthConsent {...PROPS} failed />);

    expect(screen.getByRole("alert")).toHaveTextContent(
      "That did not go through",
    );
  });

  test("falls back to a neutral name when the client has none", () => {
    render(<OAuthConsent {...PROPS} clientName="" />);

    expect(screen.getByText(/Authorize An application/)).toBeInTheDocument();
  });
});

describe("OAuthConsentError", () => {
  test("explains why the flow stopped", () => {
    render(<OAuthConsentError message="This link is no longer valid." />);

    expect(screen.getByText("Cannot continue")).toBeInTheDocument();
    expect(
      screen.getByText("This link is no longer valid."),
    ).toBeInTheDocument();
  });
});
