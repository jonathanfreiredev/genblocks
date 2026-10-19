import Link from "next/link";

import { AssetPlate } from "@/components/vault/asset-plate";
import type { Suggestion } from "@/lib/vault/types";

/**
 * What the agent found while it was working, as a rail the person can push along.
 *
 * A conversation is a column of words, and five blocks are not five paragraphs:
 * they are five pictures to look at, side by side, each one a way into the item
 * view. So they scroll across rather than down, and each card opens the thing it
 * shows — a suggestion nobody can click is a paragraph again.
 *
 * The rail keeps its own scroll: the dialog's viewport scrolls for the words, and
 * a sideways gesture inside the rail belongs to the rail.
 */

/** Where a card goes: the gallery, with the item dialog already open. */
function hrefFor(item: Suggestion): string {
  return `/?kind=${item.kind}&item=${item.id}`;
}

/** What a card is, in the words of the registry rather than of the model. */
const KIND_LABEL: Record<Suggestion["kind"], string> = {
  component: "Block",
  image: "Image",
};

export function SuggestionRail({ items }: { items: Suggestion[] }) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div data-slot="suggestion-rail" className="border-rule border-t pt-4">
      <p className="type-label text-ink-faint">Already in the registry</p>

      <ul className="-mx-1 mt-3 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-2">
        {items.map((item) => (
          <li
            key={`${item.kind}-${item.id}`}
            className="w-40 shrink-0 snap-start"
          >
            <Link
              href={hrefFor(item)}
              className="group focus-visible:outline-ring flex h-full flex-col gap-2 rounded-sm outline-none focus-visible:outline-2 focus-visible:outline-offset-2"
            >
              <div className="border-rule bg-panel-sunken relative aspect-[4/3] overflow-hidden border">
                {item.path ? (
                  <AssetPlate
                    path={item.path}
                    alt={item.title}
                    sizes="160px"
                    caption={item.detail}
                    className="h-full w-full"
                  />
                ) : (
                  // A block from before there were renders. Saying why the frame
                  // is empty is worth more than a blank surface.
                  <span className="type-label text-ink-faint absolute inset-0 flex items-center justify-center">
                    {item.kind === "component" ? "No render yet" : "No picture"}
                  </span>
                )}
              </div>

              {/* Two lines of title whatever the title is, so the labels below
                  line up across the rail instead of stepping down with each wrap. */}
              <p className="type-meta text-ink line-clamp-2 min-h-[2.8em] group-hover:underline">
                {item.title}
              </p>
              <span className="type-label text-ink-faint mt-auto">
                {KIND_LABEL[item.kind]}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
