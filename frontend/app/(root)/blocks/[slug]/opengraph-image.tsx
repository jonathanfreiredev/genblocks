import { cache } from "react";

import { categoryDescription } from "@/lib/seo/categories";
import {
  OG_CONTENT_TYPE,
  OG_SIZE,
  artifactDataUri,
  renderOgImage,
} from "@/lib/seo/og";
import {
  getComponent,
  getComponentBySlug,
  listCategories,
} from "@/lib/vault/api";
import { isUuid } from "@/lib/vault/links";
import type { Category } from "@/lib/vault/types";

export const alt =
  "GenBlocks — a generated UI block, scored by an independent judge";
export const size = OG_SIZE;
export const contentType = OG_CONTENT_TYPE;
export const revalidate = 86400;

const loadComponent = cache(async (slug: string) =>
  isUuid(slug) ? getComponent(slug) : getComponentBySlug(slug),
);

function findType(categories: Category[], slug: string): Category | undefined {
  return categories.find(
    (category) =>
      category.kind === "component" &&
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
    const [component, categories] = await Promise.all([
      loadComponent(slug),
      listCategories(),
    ]);

    if (component) {
      const category = categories.find(
        (one) => one.id === component.category_id,
      );
      const image = await artifactDataUri(
        component.thumbnail_path ?? component.screenshot_path,
      );

      return renderOgImage({
        eyebrow: category ? `UI block · ${category.name}` : "UI block",
        title: component.title,
        description: component.description,
        image,
        imageFit: "contain",
        footer: "Judged independently.",
      });
    }

    const category = findType(categories, slug);

    if (category) {
      return renderOgImage({
        eyebrow: "UI blocks",
        title: `${category.name} blocks, generated and scored.`,
        description: categoryDescription(
          category.slug,
          category.name,
          "blocks",
        ),
      });
    }
  } catch (error) {
    console.error(
      `opengraph-image: could not read the block or category (${String(error)})`,
    );
  }

  return renderOgImage({
    eyebrow: "UI blocks",
    title: "UI blocks, generated and scored.",
    description:
      "Live previews, copyable source and the independent judge's evidence for every block.",
  });
}
