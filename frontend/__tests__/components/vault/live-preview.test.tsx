import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test, vi } from "vitest";

import { LivePreview } from "@/components/vault/live-preview";

const COMPONENT_ID = "0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b";

afterEach(() => {
  // The theme is a class on the page, so a test that switches it would switch it
  // for the next one too.
  document.documentElement.classList.remove("dark");
});

async function preview() {
  render(<LivePreview componentId={COMPONENT_ID} title="Proof-sheet hero" />);

  return screen.findByTitle("Interactive preview: Proof-sheet hero");
}

describe("LivePreview", () => {
  test("runs the block on an opaque origin, with scripts and nothing else", async () => {
    const frame = await preview();

    // `allow-same-origin` would put generated code on this page's origin; it is
    // the one token that must never be added. Forms may fire (validation lives in
    // their handler) and may not send.
    expect(frame).toHaveAttribute("sandbox", "allow-scripts allow-forms");
    expect(frame).toHaveAttribute("referrerpolicy", "no-referrer");
    expect(frame).toHaveAttribute(
      "src",
      `/api/previews/${COMPONENT_ID}?theme=light`,
    );
  });

  test("follows the theme without reloading the block", async () => {
    const frame = (await preview()) as HTMLIFrameElement;
    const content = frame.contentWindow!;
    const post = vi.spyOn(content, "postMessage");
    const src = frame.getAttribute("src");

    act(() => {
      document.documentElement.classList.add("dark");
      window.dispatchEvent(new Event("genblocks-theme-change"));
    });

    expect(post).toHaveBeenCalledWith(
      { type: "genblocks:preview", theme: "dark" },
      "*",
    );
    // Same address: the block keeps whatever the visitor typed into it.
    expect(frame).toHaveAttribute("src", src);
  });

  test("takes its height from the page it is running", async () => {
    const frame = (await preview()) as HTMLIFrameElement;
    const source = frame.contentWindow!;

    act(() => {
      window.dispatchEvent(
        new MessageEvent("message", {
          data: { type: "genblocks:preview:size", height: 706 },
          source,
        }),
      );
    });

    expect(frame.style.height).toBe("706px");
  });

  test("ignores a size from anywhere but its own frame", async () => {
    const frame = (await preview()) as HTMLIFrameElement;

    act(() => {
      window.dispatchEvent(
        new MessageEvent("message", {
          data: { type: "genblocks:preview:size", height: 900 },
          source: window,
        }),
      );
    });

    expect(frame.style.height).toBe("420px");
  });

  test("clamps what a page may claim", async () => {
    const frame = (await preview()) as HTMLIFrameElement;
    const source = frame.contentWindow!;

    act(() => {
      window.dispatchEvent(
        new MessageEvent("message", {
          data: { type: "genblocks:preview:size", height: 0 },
          source,
        }),
      );
    });
    expect(frame.style.height).toBe("200px");

    act(() => {
      window.dispatchEvent(
        new MessageEvent("message", {
          data: { type: "genblocks:preview:size", height: 1_000_000 },
          source,
        }),
      );
    });
    expect(frame.style.height).toBe("4000px");
  });
});
