import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The framework name and version are not a secret, but they are a free hint
  // for a scanner and nothing needs them.
  poweredByHeader: false,
  experimental: {
    // Tailwind's output is small enough to travel with the document. Inlining
    // removes the stylesheet request from the critical path, which is the main
    // render-blocking cost on a cold Lighthouse visit.
    inlineCss: true,
  },
  // Item pages resolve metadata from the vault on the same request. Streaming
  // that metadata put `<meta name="description">` near the end of the body,
  // which tools that read the initial head (Lighthouse, some crawlers) missed.
  // Blocking metadata keeps the head complete; the page and metadata already
  // share the same cached reads.
  htmlLimitedBots: /.*/,
  // A redirect declared here is answered before the React tree renders, so a
  // crawler receives a real 308 instead of a streamed page with a client-side
  // destination.
  async redirects() {
    return [{ source: "/", destination: "/blocks", permanent: true }];
  },
  // The legal pages read their Markdown from `content/legal` at request time
  // because the app shell reads the session. Keep both possible project roots
  // in the server trace, and include the documents on every route so a host
  // that resolves the page differently still receives them.
  outputFileTracingIncludes: {
    "/**": [
      "./content/legal/**/*.md",
      "./frontend/content/legal/**/*.md",
      // The social-card route reads the mark from disk so Satori never fetches
      // the site it is rendering a card for.
      "./public/brand/**/*.png",
      "./frontend/public/brand/**/*.png",
    ],
  },
  images: {
    // The library never stores more than 1536px, so asking Next for a 3840px
    // variant only creates a Cloudinary transformation nobody can see.
    deviceSizes: [320, 420, 640, 750, 828, 1080, 1200, 1536],
    remotePatterns: [
      {
        // Block renders and stock images live on Cloudinary, so the repository
        // and the database carry a public id instead of bytes.
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
    ],
  },
};

export default nextConfig;
