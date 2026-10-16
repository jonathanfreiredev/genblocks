import Link from "next/link";
import type { ReactNode } from "react";

import { AssetPlate } from "@/components/vault/asset-plate";
import { accessionMark, dimensions, formatDate } from "@/lib/vault/format";
import type { ComponentSummary, Image } from "@/lib/vault/types";

/**
 * The gallery is a proof sheet: cells that share their rules, never floating
 * tiles. Every cell answers the same three questions in the same order — which
 * item, what it is, and when it joined the registry — so the sheet can be read
 * at speed instead of admired one card at a time.
 */
export function ItemGrid({ children }: { children: ReactNode }) {
  return (
    <ul
      data-slot="item-grid"
      className="border-rule border-t border-l sm:grid sm:grid-cols-2 xl:grid-cols-3"
    >
      {children}
    </ul>
  );
}

function Cell({ children }: { children: ReactNode }) {
  return (
    <li data-slot="item-cell" className="border-rule flex border-r border-b">
      {children}
    </li>
  );
}

function CellHead({
  position,
  typeName,
}: {
  position: number;
  typeName: string;
}) {
  return (
    <div className="type-label text-ink-faint flex items-baseline justify-between gap-4">
      <span className="tabular-nums">{accessionMark(position)}</span>
      <span className="truncate">{typeName}</span>
    </div>
  );
}

function CellFoot({ left, right }: { left: string; right: string }) {
  return (
    <div className="type-meta border-rule text-ink-faint mt-auto flex items-baseline justify-between gap-4 border-t pt-3">
      <span className="truncate">{left}</span>
      <span className="shrink-0 tabular-nums">{right}</span>
    </div>
  );
}

/**
 * The cell's whole surface is the link that opens the item, so the specimen
 * cannot be read without being able to act on it.
 */
function Specimen({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="hover:bg-panel focus-visible:bg-panel flex w-full flex-col gap-5 p-5 transition-colors duration-150"
    >
      {children}
    </Link>
  );
}

export function ComponentCell({
  component,
  typeName,
  position,
  href,
}: {
  component: ComponentSummary;
  typeName: string;
  position: number;
  href: string;
}) {
  return (
    <Cell>
      <Specimen href={href}>
        <CellHead position={position} typeName={typeName} />

        <div className="flex flex-col gap-2">
          <h2 className="type-title">{component.title}</h2>
          <p className="type-body-sm text-ink-soft line-clamp-3">
            {component.description}
          </p>
        </div>

        <CellFoot
          left={component.slug}
          right={formatDate(component.created_at)}
        />
      </Specimen>
    </Cell>
  );
}

export function ImageCell({
  image,
  typeName,
  position,
  href,
}: {
  image: Image;
  typeName: string;
  position: number;
  href: string;
}) {
  return (
    <Cell>
      <Specimen href={href}>
        <CellHead position={position} typeName={typeName} />

        <AssetPlate
          path={image.path}
          alt={image.prompt}
          sizes="(min-width: 1280px) 400px, (min-width: 640px) 45vw, 100vw"
          caption={dimensions(image.width, image.height)}
          className="border-rule aspect-[3/2] border"
        />

        <p className="type-body-sm text-ink-soft line-clamp-2">
          {image.prompt}
        </p>

        <CellFoot
          left={image.model ?? "Unknown model"}
          right={formatDate(image.created_at)}
        />
      </Specimen>
    </Cell>
  );
}
