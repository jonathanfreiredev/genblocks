import type { MetadataRoute } from "next";

import { SITE_ORIGIN } from "@/lib/site";
import { PRIVATE_ROBOTS_PATHS } from "@/lib/seo/indexability";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        // Account and operator surfaces are closed to crawlers. The same
        // paths also answer with `X-Robots-Tag: noindex` in `proxy.ts`, so a
        // URL discovered from an old link cannot be indexed even though it is
        // disallowed here.
        disallow: [...PRIVATE_ROBOTS_PATHS],
      },
    ],
    sitemap: `${SITE_ORIGIN}/sitemap.xml`,
  };
}
