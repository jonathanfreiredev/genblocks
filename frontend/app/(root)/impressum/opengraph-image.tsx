import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt = "GenBlocks Impressum";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "Impressum",
    title: "Provider information for GenBlocks.",
    description:
      "The operator, address, VAT ID and contact details behind the registry.",
    footer: "Impressum",
  });
}
