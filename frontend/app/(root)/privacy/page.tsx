import type { Metadata } from "next";

import { LegalPage } from "@/components/legal/legal-page";
import { JsonLd, webPageJsonLd } from "@/lib/seo/json-ld";
import { pageMetadata } from "@/lib/seo/metadata";

const description =
  "What GenBlocks processes, why, who receives it, and how to exercise your data protection rights.";

export const metadata: Metadata = pageMetadata({
  title: "Privacy Notice",
  description,
  path: "/privacy",
});

export default function PrivacyPage() {
  return (
    <>
      <JsonLd
        data={webPageJsonLd({
          name: "Privacy Notice",
          description,
          path: "/privacy",
        })}
      />
      <LegalPage document="privacy" />
    </>
  );
}
