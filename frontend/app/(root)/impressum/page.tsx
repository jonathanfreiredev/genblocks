import type { Metadata } from "next";

import { LegalPage } from "@/components/legal/legal-page";

export const metadata: Metadata = {
  title: "Impressum",
  description:
    "Provider information for GenBlocks pursuant to section 5 of the German Digital Services Act.",
};

export default function ImpressumPage() {
  return <LegalPage document="imprint" />;
}
