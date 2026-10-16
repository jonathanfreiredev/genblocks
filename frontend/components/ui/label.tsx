"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

// Size and weight are intentionally unset: `FieldLabel` sets the system's
// uppercase mono label style, and a fixed `text-sm font-medium` here would
// collide with it.
function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      data-slot="label"
      className={cn(
        "flex items-center gap-2 select-none group-data-[disabled=true]:pointer-events-none group-data-[disabled=true]:opacity-50 peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        className
      )}
      {...props}
    />
  )
}

export { Label }
