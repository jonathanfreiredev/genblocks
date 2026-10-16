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
  signupAction: vi.fn(),
  signInWithGoogleAction: vi.fn(),
}));

import { toast } from "@/components/ui/toast";
import { signupAction } from "@/server/auth/auth.actions";
import { SignupForm } from "@/components/auth/signup-form";

const NAME = "Jane Doe";
const EMAIL = "jane@example.com";
const PASSWORD = "password123";

beforeEach(() => {
  vi.mocked(signupAction).mockResolvedValue({
    data: { success: true, requiresVerification: true },
  } as never);
});

function fillAndSubmit(confirmPassword: string) {
  fireEvent.change(screen.getByLabelText("Name"), { target: { value: NAME } });
  fireEvent.change(screen.getByLabelText("Email"), { target: { value: EMAIL } });
  fireEvent.change(screen.getByLabelText("Password"), {
    target: { value: PASSWORD },
  });
  fireEvent.change(screen.getByLabelText("Confirm Password"), {
    target: { value: confirmPassword },
  });
  fireEvent.click(screen.getByRole("button", { name: "Create Account" }));
}

describe("SignupForm", () => {
  test("blocks submission and toasts when the passwords do not match", async () => {
    render(<SignupForm />);

    fillAndSubmit("a-different-password");

    await waitFor(() =>
      expect(toast.add).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Passwords do not match!",
          type: "error",
        }),
      ),
    );
    expect(signupAction).not.toHaveBeenCalled();
  });

  test("sends the profile without confirmPassword and redirects to verification", async () => {
    render(<SignupForm />);

    fillAndSubmit(PASSWORD);

    await waitFor(() =>
      expect(replace).toHaveBeenCalledWith(
        `/auth/verify-email?email=${encodeURIComponent(EMAIL)}`,
      ),
    );
    expect(signupAction).toHaveBeenCalledWith({
      name: NAME,
      email: EMAIL,
      password: PASSWORD,
    });
  });

  test("toasts success and redirects home when no confirmation is required", async () => {
    vi.mocked(signupAction).mockResolvedValue({
      data: { success: true, requiresVerification: false },
    } as never);

    render(<SignupForm />);

    fillAndSubmit(PASSWORD);

    await waitFor(() =>
      expect(toast.add).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Account created successfully!",
          type: "success",
        }),
      ),
    );
    expect(replace).toHaveBeenCalledWith("/");
  });
});
