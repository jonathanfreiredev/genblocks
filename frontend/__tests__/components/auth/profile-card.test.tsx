import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/components/ui/toast", () => ({
  toast: { add: vi.fn() },
}));

vi.mock("@/server/users/users.actions", () => ({
  updateUserAction: vi.fn(),
  updateUserPasswordAction: vi.fn(),
}));

import { ProfileCard } from "@/components/auth/profile-card";
import { toast } from "@/components/ui/toast";
import { updateUserAction } from "@/server/users/users.actions";

const USER = { name: "Jane Doe", email: "jane@example.com" };

beforeEach(() => {
  vi.mocked(updateUserAction).mockResolvedValue({
    data: { success: true },
  } as never);
});

async function openProfileEditor() {
  fireEvent.click(screen.getByRole("button", { name: "Edit profile" }));
  return screen.findByLabelText("Name");
}

describe("ProfileCard", () => {
  test("shows the name and the email", () => {
    render(<ProfileCard user={USER} />);

    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("jane@example.com")).toBeInTheDocument();
  });

  test("shows a dash when the profile has no name yet", () => {
    render(<ProfileCard user={{ name: "", email: "jane@example.com" }} />);

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  test("cannot be edited in place", () => {
    render(<ProfileCard user={USER} />);

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Edit profile" }),
    ).toBeInTheDocument();
  });

  test("edits behind its own dialog", async () => {
    render(<ProfileCard user={USER} />);

    const name = await openProfileEditor();

    expect(name).toHaveValue("Jane Doe");
    expect(screen.getByLabelText("Email")).toHaveValue("jane@example.com");
  });

  test("saves the edit, toasts and closes the dialog", async () => {
    render(<ProfileCard user={USER} />);

    const name = await openProfileEditor();
    fireEvent.change(name, { target: { value: "Jane Roe" } });
    fireEvent.click(screen.getByRole("button", { name: "Update profile" }));

    await waitFor(() =>
      expect(updateUserAction).toHaveBeenCalledWith({
        name: "Jane Roe",
        email: "jane@example.com",
      }),
    );
    expect(toast.add).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Profile updated successfully!",
        type: "success",
      }),
    );
    expect(refresh).toHaveBeenCalled();
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
  });

  test("keeps the dialog open when the save fails", async () => {
    vi.mocked(updateUserAction).mockResolvedValue({
      serverError: { code: 400, message: "Nope." },
    } as never);

    render(<ProfileCard user={USER} />);

    const name = await openProfileEditor();
    fireEvent.change(name, { target: { value: "Jane Roe" } });
    fireEvent.click(screen.getByRole("button", { name: "Update profile" }));

    await waitFor(() =>
      expect(toast.add).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Profile update failed!",
          description: "Nope.",
          type: "error",
        }),
      ),
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  test("changes the password in its own dialog", async () => {
    render(<ProfileCard user={USER} />);

    fireEvent.click(screen.getByRole("button", { name: "Change password" }));

    expect(
      await screen.findByLabelText("Current Password"),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("New Password")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm Password")).toBeInTheDocument();
  });
});
