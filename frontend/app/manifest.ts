import type { MetadataRoute } from "next";

import { SITE_DESCRIPTION, SITE_NAME } from "@/lib/site";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "GenBlocks — generated UI blocks and stock images",
    short_name: SITE_NAME,
    description: SITE_DESCRIPTION,
    id: "/",
    start_url: "/blocks",
    scope: "/",
    display: "standalone",
    orientation: "any",
    background_color: "#ffffff",
    theme_color: "#ffffff",
    lang: "en",
    categories: ["design", "developer", "productivity"],
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "Browse blocks",
        short_name: "Blocks",
        description: "Generated UI blocks with live previews and source code.",
        url: "/blocks",
      },
      {
        name: "Browse images",
        short_name: "Images",
        description: "AI-generated stock images with the judge's scores.",
        url: "/images",
      },
      {
        name: "Connect an agent",
        short_name: "Agents",
        description: "Point an MCP client at the GenBlocks registry.",
        url: "/mcp",
      },
    ],
  };
}
