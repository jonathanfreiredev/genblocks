import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // The framework name and version are not a secret, but they are a free hint
  // for a scanner and nothing needs them.
  poweredByHeader: false,
  // The legal pages read their Markdown from `content/legal` at request time
  // because the app shell reads the session. Keep both possible project roots
  // in the server trace, and include the documents on every route so a host
  // that resolves the page differently still receives them.
  outputFileTracingIncludes: {
    "/**": ["./content/legal/**/*.md", "./frontend/content/legal/**/*.md"],
  },
  images: {
    // The library never stores more than 1536px, so asking Next for a 3840px
    // variant only creates a Cloudinary transformation nobody can see.
    deviceSizes: [640, 750, 828, 1080, 1200, 1536],
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
