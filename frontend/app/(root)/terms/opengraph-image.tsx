import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt = "GenBlocks terms of service";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "Terms",
    title: "The terms that apply to GenBlocks.",
    description:
      "Using the registry, the content policy, and what happens to the work you queue.",
    footer: "Terms of Use",
  });
}
