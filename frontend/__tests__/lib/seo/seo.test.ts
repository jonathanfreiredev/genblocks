import { describe, expect, test } from "vitest";

import { isPrivatePath } from "@/lib/seo/indexability";
import { serializeJsonLd } from "@/lib/seo/json-ld";
import {
  clampDescription,
  pageMetadata,
  titleFromPrompt,
} from "@/lib/seo/metadata";

describe("page metadata", () => {
  test("sets a canonical path, Open Graph and Twitter fields", () => {
    const metadata = pageMetadata({
      title: "UI Blocks",
      description: "Generated blocks with the judge's scores.",
      path: "/blocks",
    });

    expect(metadata.alternates?.canonical).toBe("/blocks");
    expect(metadata.robots).toEqual({ index: true, follow: true });
    expect(metadata.openGraph).toMatchObject({
      title: "UI Blocks",
      url: "/blocks",
      type: "website",
    });
    expect(metadata.twitter).toMatchObject({
      card: "summary_large_image",
      title: "UI Blocks",
    });
  });

  test("keeps search results out of the index", () => {
    const metadata = pageMetadata({
      title: "Search",
      description: "Search results.",
      path: "/blocks",
      noindex: true,
    });

    expect(metadata.robots).toEqual({
      index: false,
      follow: false,
      noarchive: true,
    });
  });

  test("clamps long descriptions at a word boundary", () => {
    const value = clampDescription("word ".repeat(80), 40);

    expect(value.length).toBeLessThanOrEqual(40);
    expect(value.endsWith("…")).toBe(true);
  });

  test("turns a prompt into a scannable title", () => {
    const title = titleFromPrompt(
      "A quiet reading corner in the afternoon. A second sentence should not be in the title.",
    );

    expect(title).toBe("A quiet reading corner in the afternoon.");
    expect(title).not.toContain("second sentence");
  });
});

describe("private paths", () => {
  test("covers the account, auth and operator surfaces", () => {
    expect(isPrivatePath("/tasks")).toBe(true);
    expect(isPrivatePath("/tasks/123")).toBe(true);
    expect(isPrivatePath("/profile")).toBe(true);
    expect(isPrivatePath("/admin/users")).toBe(true);
    expect(isPrivatePath("/auth/login")).toBe(true);
    expect(isPrivatePath("/oauth/consent")).toBe(true);
    expect(isPrivatePath("/api/agent/chat")).toBe(true);
  });

  test("leaves the public catalogue alone", () => {
    expect(isPrivatePath("/blocks")).toBe(false);
    expect(isPrivatePath("/blocks/hero")).toBe(false);
    expect(isPrivatePath("/about")).toBe(false);
    expect(isPrivatePath("/privacy")).toBe(false);
  });
});

describe("JSON-LD serialization", () => {
  test("cannot close the script element from user content", () => {
    const serialized = serializeJsonLd({
      name: "</script><script>alert(1)</script>",
      ampersand: "a & b",
    });

    expect(serialized).not.toContain("</script>");
    expect(serialized).toContain("\\u003c");
    expect(serialized).toContain("\\u0026");
  });
});
