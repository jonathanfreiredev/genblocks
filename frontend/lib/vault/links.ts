import type { Kind } from "@/lib/vault/types";

/** How many items a page of the gallery shows: two full rows on a wide screen. */
export const PAGE_SIZE = 12;

export interface CatalogueView {
  kind: Kind;
  /** A level-2 taxonomy slug to narrow the gallery to one type. */
  type?: string;
  /** Free text: a block's title and description, or an image's prompt. */
  q?: string;
  /** 1-based. Carried in the URL so a page is linkable. */
  page: number;
}

export interface CatalogueRequest extends CatalogueView {
  /** The item whose dialog is open, when one is. */
  item?: string;
}

type SearchParams = Record<string, string | string[] | undefined>;

function single(value: string | string[] | undefined): string | undefined {
  const first = Array.isArray(value) ? value[0] : value;
  const trimmed = first?.trim();

  return trimmed ? trimmed : undefined;
}

/**
 * Read the gallery's own URL.
 *
 * The address is the state: the kind, the filters, the page and the open item
 * all live in it, so any view can be linked to, reloaded, and returned to with
 * the browser's Back. Anything unrecognised falls back to the default view
 * rather than erroring — a link with a stale filter should still open a gallery.
 */
export function parseCatalogue(searchParams: SearchParams): CatalogueRequest {
  const page = Number(single(searchParams.page) ?? "1");

  return {
    kind: single(searchParams.kind) === "image" ? "image" : "component",
    type: single(searchParams.type),
    q: single(searchParams.q),
    page: Number.isInteger(page) && page >= 1 ? page : 1,
    item: single(searchParams.item),
  };
}

function queryFor(view: CatalogueView): URLSearchParams {
  const params = new URLSearchParams();

  if (view.kind !== "component") {
    params.set("kind", view.kind);
  }
  if (view.type) {
    params.set("type", view.type);
  }
  if (view.q) {
    params.set("q", view.q);
  }
  if (view.page > 1) {
    params.set("page", String(view.page));
  }

  return params;
}

/** The same view, with no dialog open. */
export function catalogueHref(view: CatalogueView): string {
  const query = queryFor(view).toString();

  return query ? `/?${query}` : "/";
}

/** The same view with one item's dialog open. */
export function itemHref(view: CatalogueView, itemId: string): string {
  const params = queryFor(view);
  params.set("item", itemId);

  return `/?${params.toString()}`;
}

export function offsetFor(view: CatalogueView): number {
  return (view.page - 1) * PAGE_SIZE;
}
