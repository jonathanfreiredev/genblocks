import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

const { push, replace, refresh } = vi.hoisted(() => ({
  push: vi.fn(),
  replace: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push, replace, refresh }),
}));

vi.mock("@/components/ui/toast", () => ({
  toast: { add: vi.fn() },
}));

vi.mock("@/server/auth/auth.actions", () => ({
  loginAction: vi.fn(),
}));

import { toast } from "@/components/ui/toast";
import { loginAction } from "@/server/auth/auth.actions";
import { LoginForm } from "@/components/auth/login-form";

const CREDENTIALS = { email: "user@example.com", password: "password123" };

beforeEach(() => {
  vi.mocked(loginAction).mockResolvedValue({ data: { success: true } } as never);
});

function submitCredentials() {
  fireEvent.change(screen.getByLabelText("Email"), {
    target: { value: CREDENTIALS.email },
  });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: CREDENTIALS.password },
  });
  fireEvent.click(screen.getByRole("button", { name: "Log in" }));
}

describe("LoginForm", () => {
  test("shows validation errors for invalid input and skips the action", async () => {
    const { container } = render(<LoginForm />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "not-an-email" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "short" },
    });

    // Submit directly: native `required` would block the click before Zod runs.
    const form = container.querySelector("form");
    if (!form) {
      throw new Error("Login form not found");
    }
    fireEvent.submit(form);

    expect(
      await screen.findByText("Please enter a valid email address"),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Password must be at least 8 characters long"),
    ).toBeInTheDocument();
    expect(loginAction).not.toHaveBeenCalled();
  });

  test("submits the credentials, toasts success and redirects", async () => {
    render(<LoginForm />);

    submitCredentials();

    await waitFor(() => expect(loginAction).toHaveBeenCalledWith(CREDENTIALS));
    expect(toast.add).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Logged in successfully!",
        type: "success",
      }),
    );
    expect(replace).toHaveBeenCalledWith("/");
  });

  test("toasts a generic server error", async () => {
    vi.mocked(loginAction).mockResolvedValue({
      serverError: { code: 401, message: "Incorrect email or password." },
    } as never);

    render(<LoginForm />);
    submitCredentials();

    await waitFor(() =>
      expect(toast.add).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Login failed!",
          description: "Incorrect email or password.",
          type: "error",
        }),
      ),
    );
  });

  test("offers to verify the email when it is not confirmed", async () => {
    vi.mocked(loginAction).mockResolvedValue({
      serverError: {
        code: 403,
        message: "Please confirm your email address before logging in.",
        reason: "email_not_confirmed",
      },
    } as never);

    render(<LoginForm />);
    submitCredentials();

    await waitFor(() =>
      expect(toast.add).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Email not confirmed",
          type: "warning",
        }),
      ),
    );
  });
});
