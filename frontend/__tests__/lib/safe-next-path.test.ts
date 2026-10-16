import { describe, expect, test } from "vitest";

import { safeNextPath } from "@/lib/safe-next-path";

describe("safeNextPath", () => {
  test("keeps a path on this origin, query string included", () => {
    expect(safeNextPath("/oauth/consent?authorization_id=abc")).toBe(
      "/oauth/consent?authorization_id=abc",
    );
  });

  test("falls back when there is nothing to honour", () => {
    expect(safeNextPath(undefined)).toBe("/");
    expect(safeNextPath(null)).toBe("/");
    expect(safeNextPath("")).toBe("/");
  });

  test("rejects an absolute URL", () => {
    expect(safeNextPath("https://evil.example")).toBe("/");
  });

  test("rejects a protocol-relative URL", () => {
    expect(safeNextPath("//evil.example")).toBe("/");
  });

  test("rejects a value that becomes userinfo when appended to an origin", () => {
    // Without the leading slash this yields "https://oursite.com@evil.example",
    // where the host is the attacker's.
    expect(safeNextPath("@evil.example")).toBe("/");
  });

  test("rejects a backslash, which some parsers normalise into a slash", () => {
    expect(safeNextPath("/\\evil.example")).toBe("/");
  });

  test("takes a custom fallback", () => {
    expect(safeNextPath("https://evil.example", "/profile")).toBe("/profile");
  });
});
