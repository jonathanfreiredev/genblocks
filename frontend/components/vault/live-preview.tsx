"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

import { useTheme, type Theme } from "@/components/theme-toggle";
import { previewUrl } from "@/lib/vault/preview";

/** What the frame is worth before the page has said how tall it is. */
const INITIAL_HEIGHT = 420;

/** Bounds for the frame's own height; the page's cap is applied by CSS. */
const MIN_HEIGHT = 200;
const MAX_HEIGHT = 4_000;

type SizeMessage = { type?: unknown; height?: unknown };

/**
 * Whether the page has hydrated.
 *
 * The server does not know the visitor's theme — it lives in a class the page
 * adds before paint — so the address of the frame can only be built on the
 * client. Asking here rather than setting state from an effect keeps the first
 * client render identical to the server's, which is what hydration requires.
 */
function useHydrated(): boolean {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}

/**
 * The block, running.
 *
 * The item view is not a picture of the artifact but the artifact: an iframe on a
 * sandboxed origin, with scripts and forms and nothing else. A visitor can type
 * into a field, run a validation rule or watch an animation, and none of it can
 * reach this page, the session or the network.
 *
 * `allow-forms` is there because a form's own `submit` handler is the thing a
 * visitor came to try — without it the browser blocks the event and a validated
 * form looks broken. The request it would make is still refused: the policy's
 * `form-action 'none'` closes that half, and `connect-src 'none'` closes the
 * fetch a script could try instead.
 *
 * The theme travels two ways. The address carries the one in force at mount, so
 * the first paint is already right; changes afterwards go over `postMessage` and
 * the block switches without reloading, which is what keeps a half-filled form
 * where the visitor left it. The same channel reports the page's height, so the
 * frame is as tall as the block instead of a fixed window into it — capped by the
 * item frame at `58svh`, past which the block scrolls inside.
 */
export function LivePreview({
  componentId,
  title,
}: {
  componentId: string;
  title: string;
}) {
  const frame = useRef<HTMLIFrameElement>(null);
  const { theme } = useTheme();
  const hydrated = useHydrated();
  const [height, setHeight] = useState(INITIAL_HEIGHT);
  // The first theme the block is opened with, frozen for the life of the frame:
  // changing it afterwards is a message, not a reload, so a half-filled form
  // survives the switch.
  const [openingTheme] = useState<Theme>(() =>
    typeof document === "undefined" ||
    !document.documentElement.classList.contains("dark")
      ? "light"
      : "dark",
  );
  const src = hydrated ? previewUrl(componentId, openingTheme) : null;

  useEffect(() => {
    const onMessage = (event: MessageEvent) => {
      // Only the frame this component owns may resize it.
      if (!frame.current || event.source !== frame.current.contentWindow) {
        return;
      }

      const message = event.data as SizeMessage | null;
      if (message?.type !== "genblocks:preview:size") {
        return;
      }
      if (
        typeof message.height !== "number" ||
        !Number.isFinite(message.height)
      ) {
        return;
      }

      setHeight(
        Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, Math.round(message.height))),
      );
    };

    window.addEventListener("message", onMessage);
    return () => window.removeEventListener("message", onMessage);
  }, []);

  useEffect(() => {
    // Also fires when the address lands, which is before the document is ready;
    // `onLoad` sends it again once the bridge is listening.
    if (!src) {
      return;
    }

    frame.current?.contentWindow?.postMessage(
      { type: "genblocks:preview", theme },
      "*",
    );
  }, [src, theme]);

  if (!src) {
    // One frame of the page before the address exists: the height is known and
    // the ground is the same muted surface the render sits on.
    return (
      <div
        aria-hidden
        className="bg-muted/40 mx-auto w-full max-w-6xl rounded-lg"
        style={{ height: INITIAL_HEIGHT }}
      />
    );
  }

  return (
    <iframe
      ref={frame}
      src={src}
      title={`Interactive preview: ${title}`}
      sandbox="allow-scripts allow-forms"
      referrerPolicy="no-referrer"
      onLoad={() =>
        frame.current?.contentWindow?.postMessage(
          { type: "genblocks:preview", theme },
          "*",
        )
      }
      className="bg-background mx-auto block max-h-[58svh] w-full max-w-6xl rounded-lg border-0"
      style={{ height }}
    />
  );
}
