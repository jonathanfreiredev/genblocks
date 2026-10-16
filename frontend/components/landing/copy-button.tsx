"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";
import { motion } from "motion/react";

import { Button } from "@/components/ui/button";

type CopyState = "idle" | "copied" | "error";

const FEEDBACK_MS = 1800;

/**
 * Copy affordance, shared by the hero command and the per-client snippets.
 *
 * A denied clipboard permission is stated rather than swallowed, because a
 * button that pretends to have copied is worse than one that says it could not.
 */
export function CopyButton({
  text,
  idleLabel = "Copy",
  className,
}: {
  text: string;
  idleLabel?: string;
  className?: string;
}) {
  const [state, setState] = useState<CopyState>("idle");

  async function copy() {
    if (!navigator.clipboard) {
      setState("error");
      window.setTimeout(() => setState("idle"), FEEDBACK_MS);
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
    } catch {
      setState("error");
    }

    window.setTimeout(() => setState("idle"), FEEDBACK_MS);
  }

  const label =
    state === "copied" ? "Copied" : state === "error" ? "Copy failed" : idleLabel;

  return (
    <motion.div whileTap={{ scale: 0.94 }} className={className}>
      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        onClick={copy}
        aria-label={label}
        title={label}
      >
        {state === "copied" ? (
          <Check className="size-4" />
        ) : (
          <Copy className="size-4" />
        )}
      </Button>

      {/* The label change above is not announced on its own. */}
      <span role="status" className="sr-only">
        {state === "copied" ? "Copied to the clipboard" : null}
        {state === "error" ? "Could not copy to the clipboard" : null}
      </span>
    </motion.div>
  );
}
