import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt =
  "GenBlocks — generated UI blocks with live previews and source code";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "UI blocks",
    title: "UI blocks, generated and scored.",
    description:
      "Live previews, copyable source and the independent judge's evidence for every block.",
  });
}
