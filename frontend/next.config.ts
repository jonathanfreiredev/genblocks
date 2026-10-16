import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        // The hero diagram lives on Cloudinary so the repository does not carry
        // a 1.3 MB PNG. See components/landing/hero.tsx.
        protocol: "https",
        hostname: "res.cloudinary.com",
      },
    ],
  },
};

export default nextConfig;
