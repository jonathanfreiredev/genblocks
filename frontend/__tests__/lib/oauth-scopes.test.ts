import { describe, expect, test } from "vitest";

import { describeScopes } from "@/lib/oauth-scopes";

describe("describeScopes", () => {
  test("turns the standard scopes into something a person can read", () => {
    expect(describeScopes("openid email")).toEqual([
      { id: "openid", label: "Confirm who you are" },
      { id: "email", label: "See your email address" },
    ]);
  });

  test("shows an unknown scope instead of hiding it", () => {
    expect(describeScopes("projects:read")).toEqual([
      { id: "projects:read", label: "projects:read" },
    ]);
  });

  test("copes with a missing or empty scope", () => {
    expect(describeScopes("")).toEqual([]);
    expect(describeScopes(null)).toEqual([]);
    expect(describeScopes(undefined)).toEqual([]);
  });

  test("ignores repeated spaces", () => {
    expect(describeScopes("  openid   email ")).toHaveLength(2);
  });
});
