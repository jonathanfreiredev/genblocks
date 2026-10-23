import Link from "next/link";
import type { ReactNode } from "react";

import { AssetPlate } from "@/components/vault/asset-plate";
import { dimensions } from "@/lib/vault/format";
import type { ComponentSummary, Image } from "@/lib/vault/types";

/**
 * The gallery is a wall of pictures, not a list of records.
 *
 * Each cell is a square frame the specimen fills: a block's render or a stock
 * image, cropped to the frame rather than letterboxed inside it, so the wall
 * reads as one surface instead of a set of mismatched proportions. The item
 * page shows the uncropped picture. There is no text on the wall. On hover the
 * specimen lifts a hair and the maker's name arrives under it — the only label
 * a thumbnail needs.
 */
export function ItemGrid({ children }: { children: ReactNode }) {
  return (
    <ul
      data-slot="item-grid"
      className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
    >
      {children}
    </ul>
  );
}

function Cell({
  href,
  author,
  label,
  children,
}: {
  href: string;
  author: string;
  label: string;
  children: ReactNode;
}) {
  return (
    <li data-slot="item-cell" className="min-w-0">
      <Link
        href={href}
        aria-label={label}
        className="group bg-background hover:border-foreground/20 hover:bg-muted/30 focus-visible:ring-ring focus-visible:ring-offset-background relative block aspect-square overflow-hidden rounded-xl border p-2 transition-[transform,background-color,border-color] duration-200 ease-out hover:-translate-y-0.5 focus-visible:ring-2 focus-visible:ring-offset-2"
      >
        <div className="h-full w-full pb-6 transition-transform duration-200 ease-out group-hover:-translate-y-0.5">
          {children}
        </div>

        <span className="text-muted-foreground pointer-events-none absolute inset-x-2 bottom-2 truncate text-center text-xs font-medium opacity-0 transition-opacity duration-200 group-hover:opacity-100">
          {author}
        </span>
      </Link>
    </li>
  );
}

export function ComponentCell({
  component,
  href,
  priority = false,
}: {
  component: ComponentSummary;
  href: string;
  priority?: boolean;
}) {
  // The card crop is the tighter picture; the render is what older blocks have.
  const picture = component.thumbnail_path ?? component.screenshot_path;

  return (
    <Cell
      href={href}
      author={component.author ?? "GenBlocks"}
      label={component.title}
    >
      {picture ? (
        <AssetPlate
          path={picture}
          alt={`The rendered block: ${component.title}`}
          sizes="(min-width: 1280px) 320px, (min-width: 1024px) 30vw, (min-width: 640px) 40vw, 45vw"
          caption={component.title}
          fit="cover"
          priority={priority}
          className="size-full bg-transparent"
        />
      ) : (
        <span className="text-muted-foreground flex size-full items-center justify-center p-3 text-center text-xs">
          {component.title}
        </span>
      )}
    </Cell>
  );
}

export function ImageCell({
  image,
  href,
  priority = false,
}: {
  image: Image;
  href: string;
  priority?: boolean;
}) {
  return (
    <Cell href={href} author={image.author ?? "GenBlocks"} label={image.prompt}>
      <AssetPlate
        path={image.path}
        alt={image.prompt}
        sizes="(min-width: 1280px) 320px, (min-width: 1024px) 30vw, (min-width: 640px) 40vw, 45vw"
        caption={dimensions(image.width, image.height)}
        fit="cover"
        priority={priority}
        className="size-full bg-transparent"
      />
    </Cell>
  );
}
