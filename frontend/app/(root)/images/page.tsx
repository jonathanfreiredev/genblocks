import type { Metadata } from "next";

import { CataloguePage } from "@/components/vault/catalogue-page";

export const metadata: Metadata = {
  title: "Images",
  description:
    "Stock images generated from a prompt and scored before they entered the library.",
};

export default async function ImagesPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return (
    <CataloguePage section="images" searchParams={await searchParams} />
  );
}
