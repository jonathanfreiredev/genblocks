import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, test, vi } from "vitest";

vi.mock("next/navigation", () => ({
  usePathname: () => "/blocks/alpha",
}));

vi.mock("@/server/reports/reports.actions", () => ({
  reportContentAction: vi.fn().mockResolvedValue({ data: { success: true } }),
}));

import { ReportDialog } from "@/components/reports/report-dialog";

describe("ReportDialog", () => {
  test("sends an anonymous visitor to sign in first", () => {
    render(
      <ReportDialog targetKind="component" targetId="id" signedIn={false} />,
    );

    const link = screen.getByRole("link", { name: /sign in to report/i });
    expect(link).toHaveAttribute("href", "/auth/login?next=%2Fblocks%2Falpha");
  });

  test("a signed-in visitor gets the reasons and a note field", () => {
    render(
      <ReportDialog targetKind="component" targetId="id" signedIn={true} />,
    );

    fireEvent.click(screen.getByRole("button", { name: /report this item/i }));

    expect(screen.getByText("Report this item")).toBeInTheDocument();
    expect(screen.getByLabelText(/what is wrong with it/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/anything else/i)).toBeInTheDocument();
    expect(
      screen.getByText(/removing the item is their decision/i),
    ).toBeInTheDocument();
  });
});
