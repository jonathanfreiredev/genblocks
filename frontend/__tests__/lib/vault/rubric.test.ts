import { describe, expect, test } from "vitest";

import {
  rubricFor,
  scoresFor,
  stampFor,
  weakestDimension,
} from "@/lib/vault/rubric";

describe("rubricFor", () => {
  test("a block is judged on six dimensions, an image on three", () => {
    expect(rubricFor("component")).toHaveLength(6);
    expect(rubricFor("image").map((dimension) => dimension.key)).toEqual([
      "visual",
      "prompt_fit",
      "compliance",
    ]);
  });
});

describe("scoresFor", () => {
  test("comes back in rubric order, not in the order the judge wrote", () => {
    const rows = scoresFor("image", {
      compliance: 97,
      visual: 88,
      prompt_fit: 91,
    });

    expect(rows.map(({ dimension }) => dimension.key)).toEqual([
      "visual",
      "prompt_fit",
      "compliance",
    ]);
  });

  test("ignores a dimension the judge did not score", () => {
    expect(scoresFor("component", { render: 90 })).toHaveLength(1);
  });

  test("has nothing to show without scores", () => {
    expect(scoresFor("component", null)).toEqual([]);
  });
});

describe("weakestDimension", () => {
  test("names the number that decided the verdict", () => {
    const weakest = weakestDimension({
      render: 92,
      accessibility: 88,
      visual: 54,
      copy: 41,
      novelty: 33,
      compliance: 79,
    });

    expect(weakest?.dimension).toEqual({ key: "novelty", label: "Novelty" });
    expect(weakest?.value).toBe(33);
  });

  test("reads a dimension that only the images rubric has", () => {
    const weakest = weakestDimension({ visual: 90, prompt_fit: 84 });

    expect(weakest?.dimension.label).toBe("Prompt fit");
    expect(weakest?.value).toBe(84);
  });

  test("has nothing to name without scores", () => {
    expect(weakestDimension(null)).toBeNull();
  });
});

describe("stampFor", () => {
  test("maps the artifact's fate onto the verdict stamp", () => {
    expect(stampFor("published")).toBe("pass");
    expect(stampFor("rejected")).toBe("fail");
  });

  test("leaves an unjudged attempt without a stamp", () => {
    expect(stampFor("candidate")).toBeNull();
  });
});
