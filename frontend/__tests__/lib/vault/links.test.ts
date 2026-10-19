import { describe, expect, test } from "vitest";

import {
  PAGE_SIZE,
  catalogueHref,
  itemHref,
  offsetFor,
  parseCatalogue,
  sectionFromPath,
  typeFromPath,
} from "@/lib/vault/links";

describe("parseCatalogue", () => {
  test("reads the section from the route, not the query", () => {
    expect(parseCatalogue("blocks", {})).toEqual({
      section: "blocks",
      type: undefined,
      q: undefined,
      page: 1,
    });
  });

  test("carries the type slug, the search and the page", () => {
    expect(
      parseCatalogue("images", { q: "harbour", page: "3" }, "photography"),
    ).toEqual({
      section: "images",
      type: "photography",
      q: "harbour",
      page: 3,
    });
  });

  test("takes the first value when a parameter repeats", () => {
    expect(parseCatalogue("blocks", { q: ["first", "second"] }).q).toBe(
      "first",
    );
  });

  test("falls back rather than failing on nonsense", () => {
    expect(parseCatalogue("blocks", { page: "0" }).page).toBe(1);
    expect(parseCatalogue("blocks", { page: "-4" }).page).toBe(1);
    expect(parseCatalogue("blocks", { page: "two" }).page).toBe(1);
    expect(parseCatalogue("blocks", { q: "   " }).q).toBeUndefined();
  });
});

describe("hrefs", () => {
  test("leaves a bare section bare", () => {
    expect(catalogueHref({ section: "blocks", page: 1 })).toBe("/blocks");
    expect(catalogueHref({ section: "images", page: 1 })).toBe("/images");
  });

  test("puts a category in the path and the search in the query", () => {
    expect(
      catalogueHref({ section: "images", type: "scene", q: "dawn", page: 1 }),
    ).toBe("/images/scene?q=dawn");
  });

  test("adds the page only when it is not the first", () => {
    expect(catalogueHref({ section: "blocks", page: 2 })).toBe(
      "/blocks?page=2",
    );
  });

  test("an item is an address, not a query", () => {
    expect(itemHref("images", "abc")).toBe("/images/abc");
    expect(itemHref("blocks", "abc")).toBe("/blocks/abc");
  });

  test("round-trips through the parser", () => {
    const parsed = parseCatalogue("images", { q: "dawn", page: "3" }, "scene");

    expect(parsed).toEqual({
      section: "images",
      type: "scene",
      q: "dawn",
      page: 3,
    });
  });
});

describe("where the URL is", () => {
  test("reads the section from the first segment", () => {
    expect(sectionFromPath("/blocks")).toBe("blocks");
    expect(sectionFromPath("/images/scene")).toBe("images");
    expect(sectionFromPath("/tasks")).toBe("blocks");
  });

  test("reads a type, but not an item id", () => {
    expect(typeFromPath("/blocks/hero", "blocks")).toBe("hero");
    expect(
      typeFromPath("/blocks/0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b", "blocks"),
    ).toBeUndefined();
    expect(typeFromPath("/images", "images")).toBeUndefined();
  });
});

describe("offsetFor", () => {
  test("pages from zero", () => {
    expect(offsetFor({ section: "blocks", page: 1 })).toBe(0);
    expect(offsetFor({ section: "blocks", page: 4 })).toBe(3 * PAGE_SIZE);
  });
});
