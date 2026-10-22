import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

const { replace, refresh } = vi.hoisted(() => ({
  replace: vi.fn(),
  refresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, refresh }),
}));

vi.mock("@/components/ui/toast", () => ({
  toast: { add: vi.fn() },
}));

vi.mock("@/server/users/users.actions", () => ({
  deleteUserAction: vi.fn(),
}));

import { DeleteAccountForm } from "@/components/auth/delete-account-form";
import { deleteUserAction } from "@/server/users/users.actions";

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(deleteUserAction).mockResolvedValue({
    data: { success: true },
  } as never);
});

describe("DeleteAccountForm", () => {
  test("asks for the password when the account has one", () => {
    render(<DeleteAccountForm hasPassword />);

    expect(screen.getByLabelText("Password")).toHaveAttribute(
      "type",
      "password",
    );
    expect(
      screen.queryByLabelText("Type DELETE to confirm"),
    ).not.toBeInTheDocument();
  });

  test("asks for the confirmation word when it has none", () => {
    render(<DeleteAccountForm hasPassword={false} />);

    expect(screen.getByLabelText("Type DELETE to confirm")).toBeInTheDocument();
    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
  });

  test("keeps the button disabled until the word matches exactly", () => {
    render(<DeleteAccountForm hasPassword={false} />);

    const submit = screen.getByRole("button", { name: "Delete account" });
    const input = screen.getByLabelText("Type DELETE to confirm");

    expect(submit).toBeDisabled();

    fireEvent.change(input, { target: { value: "delete" } });
    expect(submit).toBeDisabled();

    fireEvent.change(input, { target: { value: "DELETE" } });
    expect(submit).toBeEnabled();
  });

  test("deletes with the confirmation word and leaves the page", async () => {
    render(<DeleteAccountForm hasPassword={false} />);

    fireEvent.change(screen.getByLabelText("Type DELETE to confirm"), {
      target: { value: "DELETE" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Delete account" }));

    await waitFor(() =>
      expect(deleteUserAction).toHaveBeenCalledWith({
        password: "",
        confirmation: "DELETE",
      }),
    );
    expect(replace).toHaveBeenCalledWith("/");
  });
});
