import { describe, expect, test } from "vitest";

import { backendErrorMessage } from "@/lib/api-error";

const FALLBACK = "fallback message";

describe("backendErrorMessage", () => {
  test("returns a non-empty string detail as-is", () => {
    expect(backendErrorMessage("Not allowed", FALLBACK)).toBe("Not allowed");
  });

  test("ignores an empty or whitespace string", () => {
    expect(backendErrorMessage("   ", FALLBACK)).toBe(FALLBACK);
  });

  test("joins the messages of a FastAPI validation error list", () => {
    expect(
      backendErrorMessage([{ msg: "too short" }, { msg: "invalid email" }], FALLBACK),
    ).toBe("too short invalid email");
  });

  test("falls back for unknown shapes", () => {
    expect(backendErrorMessage(undefined, FALLBACK)).toBe(FALLBACK);
    expect(backendErrorMessage(null, FALLBACK)).toBe(FALLBACK);
    expect(backendErrorMessage({ unexpected: true }, FALLBACK)).toBe(FALLBACK);
    expect(backendErrorMessage([], FALLBACK)).toBe(FALLBACK);
    expect(backendErrorMessage([{ loc: ["body"] }], FALLBACK)).toBe(FALLBACK);
  });
});
