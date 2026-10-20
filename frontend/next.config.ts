import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // The library never stores more than 1536px, so asking Next for a 3840px
    // variant only creates a Cloudinary transformation nobody can see.
    deviceSizes: [640, 750, 828, 1080, 1200, 1536],
    remotePatterns: [
      {
        // The vault's stock images live on Cloudinary, so the repository and the
        // database carry a public id instead of bytes.
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
    ],
  },
};

export default nextConfig;
