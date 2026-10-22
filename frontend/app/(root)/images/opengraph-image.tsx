import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt =
  "GenBlocks — AI-generated stock images with the judge's scores";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "Stock images",
    title: "Stock images, generated and scored.",
    description:
      "The prompt, the dimensions and the independent judge's evidence behind every picture.",
  });
}
