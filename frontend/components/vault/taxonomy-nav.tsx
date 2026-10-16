import Link from "next/link";

import { cn } from "@/lib/utils";
import { catalogueHref, type CatalogueView } from "@/lib/vault/links";
import type { Category, Kind } from "@/lib/vault/types";

const KINDS: { kind: Kind; label: string }[] = [
  { kind: "component", label: "Blocks" },
  { kind: "image", label: "Images" },
];

/**
 * The two kinds, as primary navigation.
 *
 * Real links rather than tabs: they change the address, they open in a new tab,
 * and the underline the system gives navigation is the same one an active item
 * wears. Switching kind drops the filter and the search on purpose — a type
 * slug and a block's title mean nothing over in the image library.
 */
export function KindNav({ view }: { view: CatalogueView }) {
  return (
    <nav aria-label="Sections" className="flex items-baseline gap-6">
      {KINDS.map(({ kind, label }) => {
        const active = view.kind === kind;

        return (
          <Link
            key={kind}
            href={catalogueHref({ kind, page: 1 })}
            aria-current={active ? "page" : undefined}
            className={cn(
              "type-label underline-offset-[6px] transition-colors duration-150",
              active
                ? "text-ink underline decoration-2"
                : "text-ink-faint hover:text-ink hover:underline",
            )}
          >
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

function TypeLink({
  view,
  active,
  label,
  slug,
}: {
  view: CatalogueView;
  active: boolean;
  label: string;
  slug?: string;
}) {
  return (
    <Link
      href={catalogueHref({ kind: view.kind, type: slug, q: view.q, page: 1 })}
      aria-current={active ? "page" : undefined}
      className={cn(
        "type-meta shrink-0 underline-offset-4 transition-colors duration-150 lg:shrink",
        active
          ? "text-ink underline decoration-2"
          : "text-ink-soft hover:text-ink hover:underline",
      )}
    >
      {label}
    </Link>
  );
}

/**
 * The level-2 types of the kind on screen.
 *
 * A column on a wide screen and a scrollable row on a phone, from the same
 * markup: the filter rail is the taxonomy, so it should not become a second,
 * different list on a smaller screen.
 */
export function TaxonomyNav({
  view,
  types,
}: {
  view: CatalogueView;
  types: Category[];
}) {
  return (
    <nav
      aria-label="Types"
      className="flex gap-x-5 overflow-x-auto pb-1 lg:flex-col lg:gap-y-2 lg:overflow-visible lg:pb-0"
    >
      <TypeLink view={view} active={!view.type} label="All types" />

      {types.map((type) => (
        <TypeLink
          key={type.id}
          view={view}
          active={view.type === type.slug}
          label={type.name}
          slug={type.slug}
        />
      ))}
    </nav>
  );
}
