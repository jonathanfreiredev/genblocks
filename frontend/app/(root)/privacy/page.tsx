import type { Metadata } from "next";

import { LegalPage } from "@/components/legal/legal-page";

export const metadata: Metadata = {
  title: "Privacy",
  description:
    "What GenBlocks processes, why, who receives it, and how to exercise your data protection rights.",
};

export default function PrivacyPage() {
  return <LegalPage document="privacy" />;
}
