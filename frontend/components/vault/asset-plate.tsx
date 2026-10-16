"use client";

import Image from "next/image";
import { useState } from "react";

import { cn } from "@/lib/utils";
import { assetUrl } from "@/lib/vault/asset";

/**
 * The picture an image row points at, or an honest frame when there is none.
 *
 * A row can hold a public id whose asset has not been delivered yet, and a
 * deployment can have no cloud configured at all. Both cases say what the
 * picture is — the model and the size — rather than showing a broken image, and
 * the caller's caption underneath carries the prompt either way.
 */
export function AssetPlate({
  path,
  alt,
  sizes,
  caption,
  className,
}: {
  path: string;
  alt: string;
  sizes: string;
  /** What is known about a missing asset: the model and the dimensions. */
  caption: string;
  className?: string;
}) {
  const src = assetUrl(path, 1200);
  const [unavailable, setUnavailable] = useState(false);

  return (
    <div className={cn("bg-panel-sunken relative overflow-hidden", className)}>
      {src && !unavailable ? (
        <Image
          src={src}
          alt={alt}
          fill
          sizes={sizes}
          onError={() => setUnavailable(true)}
          className="object-cover"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col justify-end gap-1.5 p-4">
          <span className="type-label text-ink-faint">Awaiting asset</span>
          <span className="type-meta text-ink-faint">{caption}</span>
        </div>
      )}
    </div>
  );
}
