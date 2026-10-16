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

  test("shortens an id, which has no name of its own", () => {
    expect(
      buildBreadcrumbs("/tasks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b"),
    ).toEqual([
      { label: "Home", href: "/" },
      { label: "Tasks", href: "/tasks" },
      {
        label: "0199f1ab",
        href: "/tasks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
      },
    ]);
  });
});
