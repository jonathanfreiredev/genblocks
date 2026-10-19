import Link from "next/link";

import { AssetPlate } from "@/components/vault/asset-plate";
import { itemHref, KIND_SECTION } from "@/lib/vault/links";
import type { Suggestion } from "@/lib/vault/types";

/**
 * What the agent found while it was working, as a rail the person can push along.
 *
 * A conversation is a column of words, and five blocks are not five paragraphs:
 * they are five pictures to look at, side by side, each one a way into the item
 * page. So they scroll across rather than down, and each card opens the thing it
 * shows — a suggestion nobody can click is a paragraph again.
 */

/** Where a card goes: the item page of the section it belongs to. */
function hrefFor(item: Suggestion): string {
  return itemHref(KIND_SECTION[item.kind], item.id);
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
    <div data-slot="suggestion-rail" className="border-t pt-4">
      <p className="text-muted-foreground text-xs font-medium tracking-wide uppercase">
        Already in the registry
      </p>

      <ul className="-mx-1 mt-3 flex snap-x snap-mandatory gap-3 overflow-x-auto px-1 pb-2">
        {items.map((item) => (
          <li
            key={`${item.kind}-${item.id}`}
            className="w-40 shrink-0 snap-start"
          >
            <Link
              href={hrefFor(item)}
              className="group focus-visible:ring-ring flex h-full flex-col gap-2 rounded-lg outline-none focus-visible:ring-2"
            >
              <div className="bg-muted relative aspect-[4/3] overflow-hidden rounded-lg border">
                {item.path ? (
                  <AssetPlate
                    path={item.path}
                    alt={item.title}
                    sizes="160px"
                    caption={item.detail}
                    className="h-full w-full"
                  />
                ) : (
                  <span className="text-muted-foreground absolute inset-0 flex items-center justify-center px-2 text-center text-xs">
                    {item.kind === "component" ? "No render yet" : "No picture"}
                  </span>
                )}
              </div>

              <p className="line-clamp-2 min-h-[2.8em] text-xs font-medium group-hover:underline">
                {item.title}
              </p>
              <span className="text-muted-foreground mt-auto text-xs">
                {KIND_LABEL[item.kind]}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
