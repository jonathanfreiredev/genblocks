import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt = "About GenBlocks — a public registry of generated work";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "About",
    title: "A public registry of generated work.",
    description:
      "How a block or image reaches the catalogue, what the judge measures, and how the work can be reused.",
  });
}
