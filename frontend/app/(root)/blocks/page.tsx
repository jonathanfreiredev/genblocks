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
  const view = parseCatalogue("blocks", await searchParams);
  const page = view.page;

  return pageMetadata({
    title: page > 1 ? `UI Blocks — Page ${page}` : "UI Blocks",
    description: catalogueIntro("blocks"),
    path: view.q ? "/blocks" : page > 1 ? `/blocks?page=${page}` : "/blocks",
    noindex: Boolean(view.q),
  });
}

export default async function BlocksPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return <CataloguePage section="blocks" searchParams={await searchParams} />;
}
