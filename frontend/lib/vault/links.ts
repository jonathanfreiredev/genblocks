import type { Kind } from "@/lib/vault/types";

/** How many items a page of a section shows. */
export const PAGE_SIZE = 12;

/** The two public addresses the product has. Blocks are the default. */
export type Section = "blocks" | "images";

export const SECTION_KIND: Record<Section, Kind> = {
  blocks: "component",
  images: "image",
};

export const KIND_SECTION: Record<Kind, Section> = {
  component: "blocks",
  image: "images",
};

export interface CatalogueView {
  section: Section;
  /** A level-2 taxonomy slug, carried in the path. */
  type?: string;
  /** Free text: a block's title and description, or an image's prompt. */
  q?: string;
  /** 1-based. Carried in the URL so a page is linkable. */
  page: number;
}

type SearchParams = Record<string, string | string[] | undefined>;

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function isUuid(value: string): boolean {
  return UUID.test(value);
}

export function sectionFromPath(pathname: string): Section {
  return pathname.startsWith("/images") ? "images" : "blocks";
}

/** The type slug a path names, or `undefined` when it names a list or an item. */
export function typeFromPath(
  pathname: string,
  section: Section,
  typeSlugs: readonly string[],
): string | undefined {
  const segments = pathname.split("/").filter(Boolean);

  if (segments[0] !== section || !segments[1] || isUuid(segments[1])) {
    return undefined;
  }

  // An item slug is a word too. Only a slug the taxonomy knows is a type; the
  // rest is the item at this address.
  return typeSlugs.includes(segments[1]) ? segments[1] : undefined;
}

function single(value: string | string[] | undefined): string | undefined {
  const first = Array.isArray(value) ? value[0] : value;
  const trimmed = first?.trim();

  return trimmed ? trimmed : undefined;
}

/**
 * Read the catalogue's own URL.
 *
 * The section and the type are path segments, so a view can be linked to and the
 * breadcrumb never has to ask the browser what is selected. Search and page are
 * the two things that do not deserve a path of their own yet.
 */
export function parseCatalogue(
  section: Section,
  searchParams: SearchParams,
  typeSlug?: string,
): CatalogueView {
  const page = Number(single(searchParams.page) ?? "1");

  return {
    section,
    type: typeSlug,
    q: single(searchParams.q),
    page: Number.isInteger(page) && page >= 1 ? page : 1,
  };
}

export function catalogueHref(view: CatalogueView): string {
  const path = view.type ? `/${view.section}/${view.type}` : `/${view.section}`;
  const params = new URLSearchParams();

  if (view.q) {
    params.set("q", view.q);
  }
  if (view.page > 1) {
    params.set("page", String(view.page));
  }

  const query = params.toString();

  return query ? `${path}?${query}` : path;
}

export function itemHref(section: Section, slug: string): string {
  return `/${section}/${slug}`;
}

export function offsetFor(view: CatalogueView): number {
  return (view.page - 1) * PAGE_SIZE;
}
