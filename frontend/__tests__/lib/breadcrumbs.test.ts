import { describe, expect, test } from "vitest";

import { buildBreadcrumbs } from "@/lib/breadcrumbs";
import type { Category } from "@/lib/vault/types";

const CATEGORIES: Category[] = [
  {
    id: "hero",
    parent_id: "components",
    kind: "component",
    slug: "hero",
    name: "Hero",
    level: 2,
  },
];

describe("buildBreadcrumbs", () => {
  test("has no trail at the root, which redirects", () => {
    expect(buildBreadcrumbs("/")).toEqual([]);
  });

  test("the section is the first and current crumb", () => {
    expect(buildBreadcrumbs("/blocks")).toEqual([{ label: "Blocks" }]);
    expect(buildBreadcrumbs("/images")).toEqual([{ label: "Images" }]);
  });

  test("a type hangs off the section", () => {
    expect(buildBreadcrumbs("/blocks/hero", CATEGORIES)).toEqual([
      { label: "Blocks", href: "/blocks" },
      { label: "Hero" },
    ]);
    expect(buildBreadcrumbs("/images/hero", CATEGORIES)).toEqual([
      { label: "Images", href: "/images" },
    ]);
  });

  test("an item stops at its section: the h1 below names it", () => {
    expect(
      buildBreadcrumbs(
        "/blocks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b",
        CATEGORIES,
      ),
    ).toEqual([{ label: "Blocks", href: "/blocks" }]);
  });

  test("tasks keep the old trail, with a short id", () => {
    expect(buildBreadcrumbs("/tasks")).toEqual([{ label: "Your tasks" }]);
    expect(
      buildBreadcrumbs("/tasks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b"),
    ).toEqual([{ label: "Your tasks", href: "/tasks" }, { label: "0199f1ab" }]);
  });

  test("a single page is its own crumb", () => {
    expect(buildBreadcrumbs("/profile")).toEqual([{ label: "Profile" }]);
  });

  test("ignores a trailing slash", () => {
    expect(buildBreadcrumbs("/blocks/")).toEqual(buildBreadcrumbs("/blocks"));
  });
});
