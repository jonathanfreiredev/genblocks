"use client";

import Image from "next/image";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { assetUrl } from "@/lib/vault/asset";

/**
 * The picture an artifact points at, or an honest frame when there is none.
 *
 * `contain` is for the gallery and the item view: a block's render has its own
 * proportions and cropping it to a square would hide the composition the judge
 * scored. `cover` stays the default for surfaces that are already a crop.
 */
export function AssetPlate({
  path,
  alt,
  sizes,
  caption,
  fit = "cover",
  className,
}: {
  path: string;
  alt: string;
  sizes: string;
  /** What is known about a missing asset: the model and the dimensions. */
  caption: string;
  fit?: "cover" | "contain";
  className?: string;
}) {
  const src = assetUrl(path, 1200);
  const [unavailable, setUnavailable] = useState(false);

  return (
    <div className={cn("bg-muted relative overflow-hidden", className)}>
      {src && !unavailable ? (
        <Image
          src={src}
          alt={alt}
          fill
          sizes={sizes}
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
