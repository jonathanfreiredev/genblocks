import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, test, vi } from "vitest";

const { refresh } = vi.hoisted(() => ({ refresh: vi.fn() }));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ refresh }),
}));

vi.mock("@/components/ui/toast", () => ({
  toast: { add: vi.fn() },
}));

vi.mock("@/server/oauth/oauth.actions", () => ({
  revokeAppAction: vi.fn(),
}));

import { ConnectedAppsCard } from "@/components/auth/connected-apps-card";
import { toast } from "@/components/ui/toast";
import { revokeAppAction } from "@/server/oauth/oauth.actions";

const CONNECTED = {
  ok: true as const,
  apps: [
    {
      clientId: "client-1",
      name: "Claude Code",
      scopes: ["openid", "email"],
      grantedAt: "Oct 13, 2026",
    },
  ],
};

beforeEach(() => {
  vi.mocked(revokeAppAction).mockResolvedValue({
    data: { success: true },
  } as never);
});

async function openConfirmation() {
  fireEvent.click(screen.getByRole("button", { name: "Disconnect" }));
  return screen.findByText("Disconnect Claude Code?");
}

describe("ConnectedAppsCard", () => {
  test("lists each application with its scopes and date", () => {
    render(<ConnectedAppsCard result={CONNECTED} />);

    expect(screen.getByText("Claude Code")).toBeInTheDocument();
    expect(
      screen.getByText("Confirm who you are, See your email address"),
    ).toBeInTheDocument();
    expect(screen.getByText("Connected Oct 13, 2026")).toBeInTheDocument();
  });

  test("says when nothing is connected", () => {
    render(<ConnectedAppsCard result={{ ok: true, apps: [] }} />);

    expect(
      screen.getByText("No application is connected to your account."),
    ).toBeInTheDocument();
  });

  test("admits when the grants could not be read", () => {
    render(<ConnectedAppsCard result={{ ok: false }} />);

    expect(
      screen.getByText(/Your connected applications could not be loaded/),
    ).toBeInTheDocument();
  });

  test("names the application before cutting it off", async () => {
    render(<ConnectedAppsCard result={CONNECTED} />);

    await openConfirmation();

    expect(revokeAppAction).not.toHaveBeenCalled();
  });

  test("cancelling keeps the grant", async () => {
    render(<ConnectedAppsCard result={CONNECTED} />);

    await openConfirmation();
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

    expect(revokeAppAction).not.toHaveBeenCalled();
  });

  test("revokes the grant, toasts and refreshes the list", async () => {
    render(<ConnectedAppsCard result={CONNECTED} />);

    await openConfirmation();
    fireEvent.click(screen.getByRole("button", { name: "Yes, disconnect" }));

    await waitFor(() =>
      expect(revokeAppAction).toHaveBeenCalledWith({ clientId: "client-1" }),
    );
    expect(toast.add).toHaveBeenCalledWith(
      expect.objectContaining({
        title: "Claude Code disconnected",
        type: "success",
      }),
    );
    expect(refresh).toHaveBeenCalled();
  });

  test("toasts when the revocation fails", async () => {
    vi.mocked(revokeAppAction).mockResolvedValue({
      serverError: { code: 400, message: "Nope." },
    } as never);

    render(<ConnectedAppsCard result={CONNECTED} />);

    await openConfirmation();
    fireEvent.click(screen.getByRole("button", { name: "Yes, disconnect" }));

    await waitFor(() =>
      expect(toast.add).toHaveBeenCalledWith(
        expect.objectContaining({
          title: "Could not disconnect the application",
          description: "Nope.",
          type: "error",
        }),
      ),
    );
    expect(refresh).not.toHaveBeenCalled();
  });
});
