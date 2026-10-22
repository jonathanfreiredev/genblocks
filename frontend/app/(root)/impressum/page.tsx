import type { Metadata } from "next";

import { LegalPage } from "@/components/legal/legal-page";
import { JsonLd, webPageJsonLd } from "@/lib/seo/json-ld";
import { pageMetadata } from "@/lib/seo/metadata";

const description =
  "Provider information for GenBlocks pursuant to section 5 of the German Digital Services Act.";

export const metadata: Metadata = pageMetadata({
  title: "Impressum",
  description,
  path: "/impressum",
});

export default function ImpressumPage() {
  return (
    <>
      <JsonLd
        data={webPageJsonLd({
          name: "Impressum",
          description,
          path: "/impressum",
        })}
      />
      <LegalPage document="imprint" />
    </>
  );
}
