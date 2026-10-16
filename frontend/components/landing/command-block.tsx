"use client";

import { useEffect, useState } from "react";
import { useReducedMotion } from "motion/react";

import { CopyButton } from "@/components/landing/copy-button";

/**
 * Three lines, so the block stays readable at the width of the hero copy. All three
 * are needed: `docker-compose.yml` wants both app environment files to exist, so
 * copying only the stack's own leaves `docker compose up` failing on a fresh clone.
 */
const COMMAND = [
  "git clone https://github.com/jonathanfreiredev/mcp-stack && cd mcp-stack",
  "cp .env.example .env && cp backend/.env.example backend/.env",
  "cp frontend/.env.example frontend/.env && docker compose up",
].join("\n");

const TYPING_INTERVAL_MS = 16;
const TYPING_STEP = 2;

/**
 * The command, offered in the form it is actually used: typeable and copyable.
 *
 * It types itself once on arrival, which is the page's one authored motion, and
 * that is why the visible text is marked decorative and the real command travels
 * in a screen-reader copy underneath: the DOM must not be one character long
 * while the animation runs.
 */
export function CommandBlock() {
  const [typed, setTyped] = useState("");
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => {
    // Reduced motion takes the same path with an instant step, so the command
    // never arrives through an animation and no state is set during the effect
    // body itself.
    const step = prefersReducedMotion ? COMMAND.length : TYPING_STEP;
    const interval = prefersReducedMotion ? 0 : TYPING_INTERVAL_MS;

    let cursor = 0;
    const timer = window.setInterval(() => {
      cursor += step;
      setTyped(COMMAND.slice(0, cursor));
      if (cursor >= COMMAND.length) {
        window.clearInterval(timer);
      }
    }, interval);

    return () => window.clearInterval(timer);
  }, [prefersReducedMotion]);

  const isTyping = typed.length < COMMAND.length;

  return (
    <div className="border-border relative rounded-xl border p-5">
      <div className="flex items-start justify-between gap-4">
        <pre
          aria-hidden="true"
          className="min-w-0 font-mono text-xs leading-6 break-words whitespace-pre-wrap sm:text-sm"
        >
          {typed}
          {isTyping ? (
            <span className="bg-foreground inline-block h-4 w-2 translate-y-0.5" />
          ) : null}
        </pre>

        <span className="sr-only">{COMMAND}</span>

        <CopyButton
          text={COMMAND}
          idleLabel="Copy the commands"
          className="-mt-1 shrink-0"
        />
      </div>
    </div>
  );
}
