import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { BlockItem } from "@/components/vault/block-item";
import { CataloguePage } from "@/components/vault/catalogue-page";
import {
  getComponent,
  listCategories,
  listComponentGenerations,
} from "@/lib/vault/api";
import { isUuid } from "@/lib/vault/links";

export const metadata: Metadata = {
  title: "Block",
};

type Params = { slug: string };
type SearchParams = Record<string, string | string[] | undefined>;

/**
 * One address serves a category and an item: a type is a word, an item is a
 * uuid. The shape is the same as the rest of the vault, so a link to either
 * survives a reload and the Back button.
 */
export default async function BlockRoute({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await params;

  if (!isUuid(slug)) {
    return (
      <CataloguePage
        section="blocks"
        typeSlug={slug}
        searchParams={await searchParams}
      />
    );
  }

  const component = await getComponent(slug);
  if (!component) {
    notFound();
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
