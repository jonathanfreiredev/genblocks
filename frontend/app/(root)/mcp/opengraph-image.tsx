import { OG_CONTENT_TYPE, OG_SIZE, renderOgImage } from "@/lib/seo/og";

export const alt = "GenBlocks — connect an AI agent over MCP";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

export default async function Image() {
  return renderOgImage({
    eyebrow: "MCP",
    title: "Connect an agent to the registry.",
    description:
      "Point Claude Code, Cursor, opencode or n8n at GenBlocks and let it search, read and build.",
  });
}
