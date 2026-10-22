import type { Metadata } from "next";
import { permanentRedirect } from "next/navigation";
import { cache } from "react";

import { CataloguePage } from "@/components/vault/catalogue-page";
import { ImageItem } from "@/components/vault/image-item";
import { categoryDescription } from "@/lib/seo/categories";
import { JsonLd, breadcrumbJsonLd, imageObjectJsonLd } from "@/lib/seo/json-ld";
import { pageMetadata, titleFromPrompt } from "@/lib/seo/metadata";
import { getImage, getImageBySlug, listCategories } from "@/lib/vault/api";
import { isUuid, parseCatalogue } from "@/lib/vault/links";
import { getSession } from "@/server/auth/auth.lib";
import type { Category } from "@/lib/vault/types";

type Params = { slug: string };
type SearchParams = Record<string, string | string[] | undefined>;

const loadCategories = cache(listCategories);

/** One picture by its readable address, or an old id link, once per request. */
const loadImage = cache(async (slug: string) =>
  isUuid(slug) ? getImage(slug) : getImageBySlug(slug),
);

function findType(categories: Category[], slug: string): Category | undefined {
  return categories.find(
    (category) =>
      category.kind === "image" &&
      category.level === 2 &&
      category.slug === slug,
  );
}

/**
 * A picture is addressed by its slug; an old id link redirects to it. A word
 * the taxonomy knows is the image catalogue for that type.
 */
export async function generateMetadata({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}): Promise<Metadata> {
  const { slug } = await params;
  const [image, categories] = await Promise.all([
    loadImage(slug),
    loadCategories(),
  ]);

  if (image) {
    const category = categories.find((one) => one.id === image.category_id);
    const title = titleFromPrompt(image.prompt);

    return pageMetadata({
      title,
      description: `${image.prompt} ${image.width} × ${image.height} ${
        category?.name ?? "Generated image"
      }.`,
      path: `/images/${image.slug ?? image.id}`,
      type: "article",
      publishedTime: image.created_at,
      authors: [image.author ?? "GenBlocks"],
      section: category?.name,
    });
  }

  const category = findType(categories, slug);

  if (category) {
    const view = parseCatalogue("images", await searchParams, category.slug);

    return pageMetadata({
      title:
        view.page > 1
          ? `${category.name} Stock Images — Page ${view.page}`
          : `${category.name} Stock Images`,
      description: categoryDescription(category.slug, category.name, "images"),
      path: view.q
        ? `/images/${category.slug}`
        : view.page > 1
          ? `/images/${category.slug}?page=${view.page}`
          : `/images/${category.slug}`,
      noindex: Boolean(view.q),
    });
  }

  return pageMetadata({
    title: "Image not found",
    description: "This image is not in the library.",
    path: `/images/${slug}`,
    noindex: true,
  });
}

export default async function ImageRoute({
  params,
  searchParams,
}: {
  params: Promise<Params>;
  searchParams: Promise<SearchParams>;
}) {
  const { slug } = await params;
  const image = await loadImage(slug);

  if (!image) {
    return (
      <CataloguePage
        section="images"
        typeSlug={slug}
        searchParams={await searchParams}
      />
    );
  }

  if (image.slug && slug !== image.slug) {
    permanentRedirect(`/images/${image.slug}`);
  }

  const [categories, session] = await Promise.all([
    loadCategories(),
    getSession(),
  ]);
  const category = categories.find((one) => one.id === image.category_id);
  const categoryName = category?.name ?? "Image";

  return (
    <>
      <JsonLd data={imageObjectJsonLd(image, categoryName)} />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Images", path: "/images" },
          ...(category
            ? [
                {
                  name: category.name,
                  path: `/images/${category.slug}`,
                },
              ]
            : []),
          { name: titleFromPrompt(image.prompt) },
        ])}
      />
      <ImageItem
        image={image}
        categoryName={categoryName}
        signedIn={session !== null}
      />
    </>
  );
}
