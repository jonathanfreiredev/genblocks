import { describe, expect, test } from "vitest";

import {
  accessionMark,
  dimensions,
  elapsed,
  formatDate,
  formatTime,
} from "@/lib/vault/format";

describe("dates", () => {
  test("reads a timestamp in UTC, so server and browser agree", () => {
    expect(formatDate("2026-10-16T23:30:00Z")).toBe("16 Oct 2026");
    expect(formatTime("2026-10-16T23:30:00Z")).toBe("23:30");
  });

  test("pads the clock so the column stays aligned", () => {
    expect(formatTime("2026-10-16T04:05:00Z")).toBe("04:05");
  });
});

describe("accessionMark", () => {
  test("pads to three figures", () => {
    expect(accessionMark(1)).toBe("№ 001");
    expect(accessionMark(128)).toBe("№ 128");
  });
});

describe("dimensions", () => {
  test("uses the multiplication sign, not an x", () => {
    expect(dimensions(1536, 1024)).toBe("1536 × 1024");
  });
});

describe("elapsed", () => {
  test("says nothing about a step that has not finished", () => {
    expect(elapsed("2026-10-16T09:00:00Z", null)).toBe("—");
    expect(elapsed(null, "2026-10-16T09:00:05Z")).toBe("—");
  });

  test("reads seconds, minutes and hours", () => {
    expect(elapsed("2026-10-16T09:00:00Z", "2026-10-16T09:00:12Z")).toBe("12s");
    expect(elapsed("2026-10-16T09:00:00Z", "2026-10-16T09:02:07Z")).toBe(
      "2m 07s",
    );
    expect(elapsed("2026-10-16T09:00:00Z", "2026-10-16T10:42:00Z")).toBe(
      "1h 42m",
    );
  });
});
