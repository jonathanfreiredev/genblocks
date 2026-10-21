import Link from "next/link";

import { AssetPlate } from "@/components/vault/asset-plate";
import { buttonVariants } from "@/components/ui/button";
import type { Image } from "@/lib/vault/types";

/** The picture a standalone image task produced. */
export function ImageResult({ image }: { image: Image }) {
  return (
    <div className="flex flex-col gap-3">
      <div className="bg-muted/20 rounded-xl border p-2 sm:p-3">
        <div
          className="relative mx-auto max-h-[52svh] w-full max-w-3xl"
          style={{ aspectRatio: `${image.width} / ${image.height}` }}
        >
          <AssetPlate
            path={image.path}
            alt={image.prompt}
            sizes="(min-width: 1280px) 760px, 100vw"
            caption={`${image.width} × ${image.height}`}
            fit="contain"
            className="size-full rounded-lg"
          />
        </div>
      </div>
      <p className="text-muted-foreground text-sm">{image.prompt}</p>
      <Link
        href={`/images/${image.slug ?? image.id}`}
        prefetch={false}
        className={buttonVariants({ variant: "outline", size: "sm" })}
      >
        Open the image page
      </Link>
    </div>
  );
}
