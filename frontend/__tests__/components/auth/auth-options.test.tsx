import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
}));

vi.mock("@/components/ui/toast", () => ({
  toast: { add: vi.fn() },
}));

vi.mock("@/server/auth/auth.actions", () => ({
  loginAction: vi.fn(),
  signupAction: vi.fn(),
  signInWithGoogleAction: vi.fn(),
}));

vi.mock("@/lib/auth-providers", () => ({
  isProviderEnabled: vi.fn(),
}));

import { isProviderEnabled } from "@/lib/auth-providers";
import { LoginForm } from "@/components/auth/login-form";
import { SignupForm } from "@/components/auth/signup-form";

beforeEach(() => {
  vi.mocked(isProviderEnabled).mockReturnValue(true);
});

describe("auth provider order", () => {
  test("puts Google before the email form and separates the two paths", () => {
    render(<LoginForm />);

    const google = screen.getByRole("button", {
      name: "Continue with Google",
    });
    const email = screen.getByLabelText("Email");

    expect(
      google.compareDocumentPosition(email) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText("or")).toBeInTheDocument();
    expect(google.querySelector("svg")).toHaveAttribute("aria-hidden", "true");
  });

  test("uses the same order on signup", () => {
    render(<SignupForm />);

    const google = screen.getByRole("button", {
      name: "Continue with Google",
    });
    const name = screen.getByLabelText("Name");

    expect(
      google.compareDocumentPosition(name) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(screen.getByText("or")).toBeInTheDocument();
  });

  test("omits the divider when only email is enabled", () => {
    vi.mocked(isProviderEnabled).mockImplementation(
      (provider) => provider === "email",
    );

    render(<LoginForm />);

    expect(
      screen.queryByRole("button", { name: "Continue with Google" }),
    ).not.toBeInTheDocument();
    expect(screen.queryByText("or")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
  });

  test("omits the email form and divider when only Google is enabled", () => {
    vi.mocked(isProviderEnabled).mockImplementation(
      (provider) => provider === "google",
    );

    render(<SignupForm />);

    expect(
      screen.getByRole("button", { name: "Continue with Google" }),
    ).toBeInTheDocument();
    expect(screen.queryByLabelText("Email")).not.toBeInTheDocument();
    expect(screen.queryByText("or")).not.toBeInTheDocument();
  });
});
