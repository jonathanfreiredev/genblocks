import { cache } from "react";

import { categoryDescription } from "@/lib/seo/categories";
import { titleFromPrompt } from "@/lib/seo/metadata";
import {
  OG_CONTENT_TYPE,
  OG_SIZE,
  artifactDataUri,
  renderOgImage,
} from "@/lib/seo/og";
import { getImage, getImageBySlug, listCategories } from "@/lib/vault/api";
import { isUuid } from "@/lib/vault/links";
import type { Category } from "@/lib/vault/types";

export const alt =
  "GenBlocks — an AI-generated stock image with the judge's scores";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

const loadImage = cache(async (slug: string) =>
  isUuid(slug) ? getImage(slug) : getImageBySlug(slug),
);

function findType(categories: Category[], slug: string): Category | undefined {
  return categories.find(
    (category) =>
      category.kind === "image" &&
      category.level === 2 &&
      category.slug === slug,
  );
}

export default async function Image({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  try {
    const [image, categories] = await Promise.all([
      loadImage(slug),
      listCategories(),
    ]);

    if (image) {
      const category = categories.find((one) => one.id === image.category_id);
      const artwork = await artifactDataUri(image.path);

      return renderOgImage({
        eyebrow: category ? `Stock image · ${category.name}` : "Stock image",
        title: titleFromPrompt(image.prompt),
        description: image.prompt,
        image: artwork,
        footer: `${image.width} × ${image.height}`,
      });
    }

    const category = findType(categories, slug);

    if (category) {
      return renderOgImage({
        eyebrow: "Stock images",
        title: `${category.name} images, generated and scored.`,
        description: categoryDescription(
          category.slug,
          category.name,
          "images",
        ),
      });
    }
  } catch (error) {
    console.error(
      `opengraph-image: could not read the image or category (${String(error)})`,
    );
  }

  return renderOgImage({
    eyebrow: "Stock images",
    title: "Stock images, generated and scored.",
    description:
      "The prompt, the dimensions and the independent judge's evidence behind every picture.",
  });
}
