import type { Metadata } from "next";

import { LegalPage } from "@/components/legal/legal-page";

export const metadata: Metadata = {
  title: "Terms",
  description:
    "The terms that apply to GenBlocks, including the content policy for blocks and generated images.",
};

export default function TermsPage() {
  return <LegalPage document="terms" />;
}
