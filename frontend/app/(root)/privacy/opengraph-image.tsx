import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt = "GenBlocks privacy notice";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "Privacy",
    title: "What GenBlocks processes, and why.",
    description:
      "The data behind the registry, who receives it, and how to exercise your rights.",
    footer: "Privacy Notice",
  });
}
