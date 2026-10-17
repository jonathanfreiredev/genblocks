import type { ComponentProps } from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

// Coral is taxonomy in this system, so a chip is the only place a large coral
// area is allowed. `active` is the selected filter; `quiet` is the same chip at
// rest; `outline` is the light taxonomy control.
const categoryChipVariants = cva(
  "inline-flex w-fit shrink-0 items-center rounded-full border whitespace-nowrap transition-colors",
  {
    variants: {
      variant: {
        active: "border-transparent bg-coral text-on-coral",
        quiet:
          "border-hairline bg-background text-ink-strong hover:bg-stone-soft",
        outline:
          "border-coral-soft bg-coral/5 text-ink-strong hover:bg-coral/10",
      },
      size: {
        default: "type-body-sm px-4 py-2",
        sm: "type-body-sm px-3 py-1.5",
      },
    },
    defaultVariants: {
      variant: "quiet",
      size: "default",
    },
  },
);

function CategoryChip({
  className,
  variant,
  size,
  ...props
}: ComponentProps<"span"> & VariantProps<typeof categoryChipVariants>) {
  return (
    <span
      data-slot="category-chip"
      data-variant={variant ?? "quiet"}
      className={cn(categoryChipVariants({ variant, size, className }))}
      {...props}
    />
  );
}

export { CategoryChip, categoryChipVariants };
