import { describe, expect, test } from "vitest";

import {
  PAGE_SIZE,
  catalogueHref,
  itemHref,
  offsetFor,
  parseCatalogue,
} from "@/lib/vault/links";

describe("parseCatalogue", () => {
  test("defaults to the blocks, first page, no filters", () => {
    expect(parseCatalogue({})).toEqual({
      kind: "component",
      type: undefined,
      q: undefined,
      page: 1,
      item: undefined,
    });
  });

  test("reads the whole view out of the address", () => {
    expect(
      parseCatalogue({
        kind: "image",
        type: "photography",
        q: "harbour",
        page: "3",
        item: "8f3a",
      }),
    ).toEqual({
      kind: "image",
      type: "photography",
      q: "harbour",
      page: 3,
      item: "8f3a",
    });
  });

  test("takes the first value when a parameter repeats", () => {
    expect(parseCatalogue({ q: ["first", "second"] }).q).toBe("first");
  });

  test("falls back to the default view rather than failing on nonsense", () => {
    expect(parseCatalogue({ kind: "banana" }).kind).toBe("component");
    expect(parseCatalogue({ page: "0" }).page).toBe(1);
    expect(parseCatalogue({ page: "-4" }).page).toBe(1);
    expect(parseCatalogue({ page: "two" }).page).toBe(1);
    expect(parseCatalogue({ q: "   " }).q).toBeUndefined();
  });
});

describe("hrefs", () => {
  test("leaves the default view bare", () => {
    expect(catalogueHref({ kind: "component", page: 1 })).toBe("/");
  });

  test("carries the filters and drops the first page", () => {
    expect(
      catalogueHref({ kind: "image", type: "scene", q: "dawn", page: 1 }),
    ).toBe("/?kind=image&type=scene&q=dawn");
  });

  test("adds the page only when it is not the first", () => {
    expect(catalogueHref({ kind: "component", page: 2 })).toBe("/?page=2");
  });

  test("opens an item inside the view it was found in", () => {
    expect(itemHref({ kind: "image", page: 1 }, "abc")).toBe(
      "/?kind=image&item=abc",
    );
  });

  test("round-trips through the parser", () => {
    const view = { kind: "image" as const, type: "scene", q: "dawn", page: 3 };
    const parsed = parseCatalogue(
      Object.fromEntries(
        new URL(catalogueHref(view), "https://x").searchParams,
      ),
    );

    expect(parsed).toEqual({ ...view, item: undefined });
  });
});

describe("offsetFor", () => {
  test("pages from zero", () => {
    expect(offsetFor({ kind: "component", page: 1 })).toBe(0);
    expect(offsetFor({ kind: "component", page: 4 })).toBe(3 * PAGE_SIZE);
  });
});
