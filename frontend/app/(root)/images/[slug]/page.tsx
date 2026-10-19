import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { CataloguePage } from "@/components/vault/catalogue-page";
import { ImageItem } from "@/components/vault/image-item";
import { getImage, listCategories } from "@/lib/vault/api";
import { isUuid } from "@/lib/vault/links";

export const metadata: Metadata = {
  title: "Image",
};

type Params = { slug: string };
type SearchParams = Record<string, string | string[] | undefined>;

export default async function ImageRoute({
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
        section="images"
        typeSlug={slug}
        searchParams={await searchParams}
      />
    );
  }

  const image = await getImage(slug);
  if (!image) {
    notFound();
  }

  const categories = await listCategories();
  const categoryName =
    categories.find((category) => category.id === image.category_id)?.name ??
    "Image";

  return <ImageItem image={image} categoryName={categoryName} />;
}
