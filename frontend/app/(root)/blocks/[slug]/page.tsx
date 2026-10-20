import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { cache } from "react";

import { BlockItem } from "@/components/vault/block-item";
import { CataloguePage } from "@/components/vault/catalogue-page";
import {
  getComponent,
  getComponentBySlug,
  listCategories,
  listComponentGenerations,
} from "@/lib/vault/api";
import { isUuid } from "@/lib/vault/links";

type Params = { slug: string };
type SearchParams = Record<string, string | string[] | undefined>;

/** One block by its readable address, or by an old id link, once per request. */
const loadComponent = cache(async (slug: string) =>
  isUuid(slug) ? getComponent(slug) : getComponentBySlug(slug),
);

/**
 * One address serves a category and an item: a type is a word the taxonomy
 * knows, an item is its slug. The page tries the item first, so the same URL
 * shape carries both; a UUID from an older link redirects to the slug.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  const component = await loadComponent(slug);

  if (!component) {
    return { title: "Block" };
  }

  return {
    title: component.title,
    description: component.description,
    alternates: { canonical: `/blocks/${component.slug}` },
  };
}

export default async function BlockRoute({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await params;
  const component = await loadComponent(slug);

  if (!component) {
    return (
      <CataloguePage
        section="blocks"
        typeSlug={slug}
        searchParams={await searchParams}
      />
    );
  }

  // A UUID still resolves, but the address a person shares is the slug.
  if (slug !== component.slug) {
    redirect(`/blocks/${component.slug}`);
  }

  const [generations, categories] = await Promise.all([
    listComponentGenerations(component.id),
    listCategories(),
  ]);

  const categoryName =
    categories.find((category) => category.id === component.category_id)
      ?.name ?? "Unfiled";

  return (
    <BlockItem
      component={component}
      generations={generations}
      categoryName={categoryName}
    />
  );
}
