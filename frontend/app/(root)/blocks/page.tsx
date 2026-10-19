import type { Metadata } from "next";

import { CataloguePage } from "@/components/vault/catalogue-page";

export const metadata: Metadata = {
  title: "Blocks",
  description:
    "UI blocks generated from a brief, each carrying the render it was published from and the scores of the judge that read it.",
};

export default async function BlocksPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  return (
    <CataloguePage section="blocks" searchParams={await searchParams} />
  );
}
