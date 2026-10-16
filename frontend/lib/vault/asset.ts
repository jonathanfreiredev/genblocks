import { env } from "@/lib/env";

/**
 * The delivery URL for a Cloudinary public id, at the width the surface needs.
 *
 * Returns `null` when there is nothing to show: no public id, or a cloud this
 * deployment has not configured. The caller renders the recipe the row was
 * generated from instead, which is the honest state of a row whose asset has
 * not been delivered yet — better than a broken image.
 */
export function assetUrl(path: string | null, width: number): string | null {
  const cloud = env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME;

  if (!path || !cloud) {
    return null;
  }

  return `https://res.cloudinary.com/${cloud}/image/upload/f_auto,q_auto,w_${width}/${path}`;
}
