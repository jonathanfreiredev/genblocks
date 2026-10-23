/**
 * The delivery URL for a Cloudinary public id, with no Cloudinary transformation
 * on it.
 *
 * Next's image optimizer fetches this original once per rendered width, resizes
 * and converts it with sharp, and caches the result. Cloudinary only stores and
 * serves the bytes; it does not charge for a transformation nobody asked for.
 *
 * The variable is read directly rather than through `lib/env`: this helper runs
 * in client components too, and importing the validated server env there pulled
 * Zod into the initial bundle of every page.
 */
export function assetUrl(path: string | null): string | null {
  const cloud = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME?.trim();

  if (!path || !cloud) {
    return null;
  }

  return `https://res.cloudinary.com/${cloud}/image/upload/${path}`;
}
