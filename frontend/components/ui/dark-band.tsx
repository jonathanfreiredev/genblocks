import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

// A full-width deep green or navy section. This is how the system adds weight:
// not with shadow, but by changing the surface and letting the content go white.
function DarkBand({
  className,
  tone = "green",
  ...props
}: ComponentProps<"section"> & { tone?: "green" | "navy" }) {
  return (
    <section
      data-slot="dark-band"
      data-tone={tone}
      className={cn(
        "text-band-foreground w-full",
        tone === "navy" ? "bg-band-alt" : "bg-band",
        className,
      )}
      {...props}
    />
  );
}

export { DarkBand };
