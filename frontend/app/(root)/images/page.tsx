import type { Metadata } from "next";

import { CataloguePage } from "@/components/vault/catalogue-page";
import { pageMetadata } from "@/lib/seo/metadata";
import { catalogueIntro } from "@/lib/seo/categories";
import { parseCatalogue } from "@/lib/vault/links";

export async function generateMetadata({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}): Promise<Metadata> {
  const view = parseCatalogue("images", await searchParams);
  const page = view.page;

  return pageMetadata({
    title: page > 1 ? `Stock Images — Page ${page}` : "Stock Images",
    description: catalogueIntro("images"),
    path: view.q ? "/images" : page > 1 ? `/images?page=${page}` : "/images",
    noindex: Boolean(view.q),
  });
}

export default async function ImagesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return <CataloguePage section="images" searchParams={await searchParams} />;
}
