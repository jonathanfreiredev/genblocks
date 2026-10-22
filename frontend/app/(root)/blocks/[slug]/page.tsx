import type { Metadata } from "next";
import { permanentRedirect } from "next/navigation";
import { cache } from "react";

import { BlockItem } from "@/components/vault/block-item";
import { CataloguePage } from "@/components/vault/catalogue-page";
import {
  JsonLd,
  breadcrumbJsonLd,
  softwareSourceCodeJsonLd,
} from "@/lib/seo/json-ld";
import { pageMetadata } from "@/lib/seo/metadata";
import { categoryDescription } from "@/lib/seo/categories";
import {
  getComponent,
  getComponentBySlug,
  listCategories,
  listComponentGenerations,
} from "@/lib/vault/api";
import { isUuid, parseCatalogue } from "@/lib/vault/links";
import { getSession } from "@/server/auth/auth.lib";
import type { Category } from "@/lib/vault/types";

type Params = { slug: string };
type SearchParams = Record<string, string | string[] | undefined>;

/** The taxonomy is read by both the metadata and the page in one request. */
const loadCategories = cache(listCategories);

/** One block by its readable address, or by an old id link, once per request. */
const loadComponent = cache(async (slug: string) =>
  isUuid(slug) ? getComponent(slug) : getComponentBySlug(slug),
);

function findType(categories: Category[], slug: string): Category | undefined {
  return categories.find(
    (category) =>
      category.kind === "component" &&
      category.level === 2 &&
      category.slug === slug,
  );
}

/**
 * One address serves a category and an item: a type is a word the taxonomy
 * knows, an item is its slug. The page tries the item first, so the same URL
 * shape carries both; a UUID from an older link redirects to the slug.
 */
export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}): Promise<Metadata> {
  const { slug } = await params;
  const [component, categories] = await Promise.all([
    loadComponent(slug),
    loadCategories(),
  ]);

  if (component) {
    const category = categories.find((one) => one.id === component.category_id);

    return pageMetadata({
      title: component.title,
      description: component.description,
      path: `/blocks/${component.slug}`,
      type: "article",
      publishedTime: component.created_at,
      authors: [component.author ?? "GenBlocks"],
      section: category?.name,
    });
  }

  const category = findType(categories, slug);

  if (category) {
    const view = parseCatalogue("blocks", await searchParams, category.slug);

    return pageMetadata({
      title:
        view.page > 1
          ? `${category.name} UI Blocks — Page ${view.page}`
          : `${category.name} UI Blocks`,
      description: categoryDescription(category.slug, category.name, "blocks"),
      path: view.q
        ? `/blocks/${category.slug}`
        : view.page > 1
          ? `/blocks/${category.slug}?page=${view.page}`
          : `/blocks/${category.slug}`,
      noindex: Boolean(view.q),
    });
  }

  return pageMetadata({
    title: "Block not found",
    description: "This block is not in the registry.",
    path: `/blocks/${slug}`,
    noindex: true,
  });
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
    permanentRedirect(`/blocks/${component.slug}`);
  }

  const [generations, categories, session] = await Promise.all([
    listComponentGenerations(component.id),
    loadCategories(),
    getSession(),
  ]);

  const category = categories.find((one) => one.id === component.category_id);
  const categoryName = category?.name ?? "Unfiled";

  return (
    <>
      <JsonLd data={softwareSourceCodeJsonLd(component, categoryName)} />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Blocks", path: "/blocks" },
          ...(category
            ? [
                {
                  name: category.name,
                  path: `/blocks/${category.slug}`,
                },
              ]
            : []),
          { name: component.title },
        ])}
      />
      <BlockItem
        component={component}
        generations={generations}
        categoryName={categoryName}
        signedIn={session !== null}
      />
    </>
  );
}
