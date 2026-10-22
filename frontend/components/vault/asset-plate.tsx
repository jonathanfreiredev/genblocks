"use client";

import Image from "next/image";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { assetUrl } from "@/lib/vault/asset";

/**
 * The picture an artifact points at, or an honest frame when there is none.
 *
 * `cover` is for the gallery: a thumbnail is a crop, and the wall should read
 * as one surface. `contain` is for the item view, where a block's render has
 * its own proportions and cropping it would hide the composition the judge
 * scored.
 */
export function AssetPlate({
  path,
  alt,
  sizes,
  caption,
  fit = "cover",
  priority = false,
  className,
}: {
  path: string;
  alt: string;
  sizes: string;
  /** What is known about a missing asset: the model and the dimensions. */
  caption: string;
  fit?: "cover" | "contain";
  /** Set on the one image that is the page's LCP, never on a grid. */
  priority?: boolean;
  className?: string;
}) {
  const src = assetUrl(path);
  const [unavailable, setUnavailable] = useState(false);

  return (
    <div className={cn("bg-muted relative overflow-hidden", className)}>
      {src && !unavailable ? (
        <Image
          src={src}
          alt={alt}
          fill
          sizes={sizes}
          priority={priority}
          onError={() => setUnavailable(true)}
          className={cn(
            "object-cover",
            fit === "contain" && "object-contain p-2 sm:p-3",
          )}
        />
      ) : (
        <div className="absolute inset-0 flex flex-col justify-end gap-1 p-3">
          <span className="text-muted-foreground text-xs font-medium">
            Awaiting asset
          </span>
          <span className="text-muted-foreground/70 text-xs">{caption}</span>
        </div>
      )}
    </div>
  );
}
