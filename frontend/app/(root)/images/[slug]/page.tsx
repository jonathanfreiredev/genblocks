import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { cache } from "react";

import { CataloguePage } from "@/components/vault/catalogue-page";
import { ImageItem } from "@/components/vault/image-item";
import { getImage, getImageBySlug, listCategories } from "@/lib/vault/api";
import { isUuid } from "@/lib/vault/links";
import { getSession } from "@/server/auth/auth.lib";

type Params = { slug: string };
type SearchParams = Record<string, string | string[] | undefined>;

/** One picture by its readable address, or by an old id link, once per request. */
const loadImage = cache(async (slug: string) =>
  isUuid(slug) ? getImage(slug) : getImageBySlug(slug),
);

/**
 * A picture is addressed by its slug; an old id link redirects to it. A word
 * the taxonomy knows is the image catalogue for that type.
 */
export async function generateMetadata({
  params,
}: {
  params: Promise<Params>;
}): Promise<Metadata> {
  const { slug } = await params;
  const image = await loadImage(slug);

  if (!image) {
    return { title: "Image" };
  }

  return {
    title: image.prompt,
    description: image.prompt,
    alternates: { canonical: `/images/${image.slug ?? image.id}` },
  };
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
    redirect(`/images/${image.slug}`);
  }

  const [categories, session] = await Promise.all([
    listCategories(),
    getSession(),
  ]);
  const categoryName =
    categories.find((category) => category.id === image.category_id)?.name ??
    "Image";

  return (
    <ImageItem
      image={image}
      categoryName={categoryName}
      signedIn={session !== null}
    />
  );
}
