import { describe, expect, test } from "vitest";

import { buildBreadcrumbs } from "@/lib/breadcrumbs";

describe("buildBreadcrumbs", () => {
  test("returns nothing for the home page", () => {
    expect(buildBreadcrumbs("/")).toEqual([]);
  });

  test("starts at home and ends at the current page", () => {
    expect(buildBreadcrumbs("/profile")).toEqual([
      { label: "Home", href: "/" },
      { label: "Profile", href: "/profile" },
    ]);
  });

  test("builds cumulative links for nested routes", () => {
    expect(buildBreadcrumbs("/settings/security")).toEqual([
      { label: "Home", href: "/" },
      { label: "Settings", href: "/settings" },
      { label: "Security", href: "/settings/security" },
    ]);
  });

  test("humanises multi-word segments", () => {
    expect(buildBreadcrumbs("/my-account")).toEqual([
      { label: "Home", href: "/" },
      { label: "My Account", href: "/my-account" },
    ]);
  });

  test("ignores a trailing slash", () => {
    expect(buildBreadcrumbs("/profile/")).toEqual(buildBreadcrumbs("/profile"));
  });
});
