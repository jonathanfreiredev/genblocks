import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const VERDICT_LABELS = {
  pass: "PASS",
  fail: "REJECTED",
} as const;

const verdictStampVariants = cva(
  "inline-flex w-fit shrink-0 items-center rounded-sm border px-1.5 py-0.5 type-label",
  {
    variants: {
      verdict: {
        pass: "border-verdict-pass/40 bg-verdict-pass-soft text-verdict-pass",
        fail: "border-verdict-fail/40 bg-verdict-fail-soft text-verdict-fail",
      },
    },
    defaultVariants: {
      verdict: "pass",
    },
  },
);

// The judge's verdict as a rubber stamp: uppercase mono, hairline border, soft
// tint. Never a pill, never an icon, and never one of the brand spot inks — the
// pair is functional, so a rejection can't be mistaken for an action. There is no
// third stamp: a block is published or it is not, and there is no retry to draw.
function VerdictStamp({
  className,
  verdict,
  children,
  ...props
}: ComponentProps<"span"> & VariantProps<typeof verdictStampVariants>) {
  return (
    <span
      data-slot="verdict-stamp"
      data-verdict={verdict ?? "pass"}
      className={cn(verdictStampVariants({ verdict, className }))}
      {...props}
    >
      {children ?? VERDICT_LABELS[verdict ?? "pass"]}
    </span>
  );
}

export { VerdictStamp, verdictStampVariants };
