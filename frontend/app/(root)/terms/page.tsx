import type { Metadata } from "next";

import { LegalPage } from "@/components/legal/legal-page";
import { JsonLd, webPageJsonLd } from "@/lib/seo/json-ld";
import { pageMetadata } from "@/lib/seo/metadata";

const description =
  "The terms that apply to GenBlocks, including the content policy for blocks and generated images.";

export const metadata: Metadata = pageMetadata({
  title: "Terms of Use",
  description,
  path: "/terms",
});

export default function TermsPage() {
  return (
    <>
      <JsonLd
        data={webPageJsonLd({
          name: "Terms of Use",
          description,
          path: "/terms",
        })}
      />
      <LegalPage document="terms" />
    </>
  );
}
