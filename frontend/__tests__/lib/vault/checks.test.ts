import { describe, expect, test } from "vitest";

import { checkRows, labelFor } from "@/lib/vault/checks";
import type { HarnessChecks } from "@/lib/vault/types";

const FOUND: HarnessChecks = {
  blocked: false,
  passed: 1,
  total: 2,
  checks: [
    { name: "typecheck", ok: true, detail: null },
    { name: "build", ok: false, detail: "vite: unexpected token" },
  ],
  violations: [],
};

describe("checkRows", () => {
  test("names each check in the order the sandbox made them", () => {
    expect(checkRows(FOUND)).toEqual([
      { label: "Types", ok: true, detail: null },
      { label: "Build", ok: false, detail: "vite: unexpected token" },
    ]);
  });

  test("says nothing about a harness no artifact went through", () => {
    expect(checkRows(null)).toEqual([]);
  });
});

describe("labelFor", () => {
  test("names a layout check after its viewport", () => {
    expect(labelFor("layout:phone")).toBe("Phone");
    expect(labelFor("layout:desktop")).toBe("Desktop");
  });

  test("names the checks the sandbox makes", () => {
    expect(labelFor("typecheck")).toBe("Types");
    expect(labelFor("lint")).toBe("Lint");
    expect(labelFor("render")).toBe("Render");
    expect(labelFor("accessibility")).toBe("Accessibility");
  });

  test("shows a check nobody has heard of under its own name", () => {
    // A check added in a later phase should appear, not vanish.
    expect(labelFor("security")).toBe("security");
  });
});
