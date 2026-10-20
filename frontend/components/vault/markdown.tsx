"use client";

import { Streamdown } from "streamdown";

import { cn } from "@/lib/utils";

/**
 * The assistant's words, rendered.
 *
 * The agent answers in Markdown — a bolded name, a short list, a link — and a
 * plain text node would show the syntax. Streamdown is the streaming-aware
 * renderer the shadcn AI examples use: it keeps incomplete emphasis and fences
 * readable while the turn is still arriving.
 *
 * The user's own message stays plain text; only the agent's answer is markup.
 */
export function Markdown({
  children,
  streaming = false,
  className,
}: {
  children: string;
  /** True while tokens are still arriving, so the parser can hold a partial block. */
  streaming?: boolean;
  className?: string;
}) {
  return (
    <Streamdown
      className={cn(
        "text-sm leading-relaxed [&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
        className,
      )}
      controls={false}
      isAnimating={streaming}
    >
      {children}
    </Streamdown>
  );
}
