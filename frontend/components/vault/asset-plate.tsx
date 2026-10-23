"use client";

import Image from "next/image";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { assetUrl } from "@/lib/vault/asset";

/**
 * The picture an artifact points at, or an honest frame when there is none.
 *
 * The whole artifact is always shown: a block's render has its own proportions
 * and a stock picture has its own crop, and framing either one by cutting it
 * hides the composition the judge scored. The plate therefore contains, and the
 * caller's frame supplies the breathing room.
 */
export function AssetPlate({
  path,
  alt,
  sizes,
  caption,
  priority = false,
  className,
}: {
  path: string;
  alt: string;
  sizes: string;
  /** What is known about a missing asset: the model and the dimensions. */
  caption: string;
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
          fetchPriority={priority ? "high" : undefined}
          decoding={priority ? "sync" : "async"}
          onError={() => setUnavailable(true)}
          className="object-contain"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col justify-end gap-1 p-3">
          <span className="text-muted-foreground text-xs font-medium">
            Awaiting asset
          </span>
          <span className="text-muted-foreground text-xs">{caption}</span>
        </div>
      )}
    </div>
  );
}
