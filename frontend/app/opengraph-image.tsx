import { OG_ALT, OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt = OG_ALT;
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;

export default async function Image() {
  return renderOgImage({
    eyebrow: "Public registry",
    title: "Generated UI blocks and stock images, scored.",
    description:
      "Browse the work, copy the code, inspect the judge's evidence, or connect an agent over MCP.",
  });
}
