import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const VERDICT_LABELS = {
  pass: "PASS",
  fail: "REJECTED",
} as const;

const verdictStampVariants = cva(
  "inline-flex w-fit shrink-0 items-center rounded-md border px-2 py-0.5 text-xs font-medium",
  {
    variants: {
      verdict: {
        pass: "border-emerald-600/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
        fail: "border-destructive/25 bg-destructive/10 text-destructive",
      },
    },
    defaultVariants: {
      verdict: "pass",
    },
  },
);

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
