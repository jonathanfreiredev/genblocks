import { env } from "@/lib/env";

/**
 * The delivery URL for a Cloudinary public id, with no Cloudinary transformation
 * on it.
 *
 * Next's image optimizer fetches this original once per rendered width, resizes
 * and converts it with sharp, and caches the result. Cloudinary only stores and
 * serves the bytes; it does not charge for a transformation nobody asked for.
 */
export function assetUrl(path: string | null): string | null {
  const cloud = env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME;

  if (!path || !cloud) {
    return null;
  }

  return `https://res.cloudinary.com/${cloud}/image/upload/${path}`;
}
