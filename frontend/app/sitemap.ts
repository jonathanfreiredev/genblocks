import type { MetadataRoute } from "next";

import { SITE_ORIGIN } from "@/lib/site";
import {
  VaultUnreadable,
  listCategories,
  listComponents,
  listImages,
} from "@/lib/vault/api";
import { assetUrl } from "@/lib/vault/asset";
import type { Category, ComponentSummary, Image } from "@/lib/vault/types";

// The catalogue reads are uncached, so the sitemap is request-time and always
// reflects a takedown or a new publication. A sitemap is fetched rarely enough
// that correctness is worth more than a cache here.
export const dynamic = "force-dynamic";

const PAGE_SIZE = 100;

const CATALOGUE_PATHS = ["/blocks", "/images"] as const;

const STATIC_PATHS = [
  "/mcp",
  "/about",
  "/privacy",
  "/terms",
  "/impressum",
] as const;

function entriesFor(paths: readonly string[]): MetadataRoute.Sitemap {
  return paths.map((path) => ({
    url: `${SITE_ORIGIN}${path}`,
  }));
}

async function everyComponent(): Promise<ComponentSummary[]> {
  const items: ComponentSummary[] = [];
  let offset = 0;

  while (true) {
    const page = await listComponents({ limit: PAGE_SIZE, offset });
    items.push(...page.items);

    offset += page.items.length;
    if (page.items.length === 0 || offset >= page.total) {
      return items;
    }
  }
}

async function everyImage(): Promise<Image[]> {
  const items: Image[] = [];
  let offset = 0;

  while (true) {
    const page = await listImages({ limit: PAGE_SIZE, offset });
    items.push(...page.items);

    offset += page.items.length;
    if (page.items.length === 0 || offset >= page.total) {
      return items;
    }
  }
}

function latest(values: string[]): Date | undefined {
  if (values.length === 0) {
    return undefined;
  }

  return new Date(
    values.reduce((newest, value) =>
      new Date(value) > new Date(newest) ? value : newest,
    ),
  );
}

function categoryEntries(
  categories: Category[],
  components: ComponentSummary[],
  images: Image[],
): MetadataRoute.Sitemap {
  const byCategory = new Map<string, string[]>();

  for (const item of [...components, ...images]) {
    const dates = byCategory.get(item.category_id) ?? [];
    dates.push(item.created_at);
    byCategory.set(item.category_id, dates);
  }

  return categories
    .filter((category) => category.level === 2)
    .flatMap((category) => {
      const dates = byCategory.get(category.id);

      // An empty type is a real address but a thin landing page. It enters the
      // sitemap the moment it has something to show.
      if (!dates || dates.length === 0) {
        return [];
      }

      return [
        {
          url: `${SITE_ORIGIN}/${
            category.kind === "component" ? "blocks" : "images"
          }/${category.slug}`,
          lastModified: latest(dates),
        },
      ];
    });
}

function componentEntries(
  components: ComponentSummary[],
): MetadataRoute.Sitemap {
  return components.map((component) => {
    const image = assetUrl(
      component.thumbnail_path ?? component.screenshot_path,
    );

    return {
      url: `${SITE_ORIGIN}/blocks/${component.slug}`,
      lastModified: new Date(component.created_at),
      ...(image ? { images: [image] } : {}),
    };
  });
}

function imageEntries(images: Image[]): MetadataRoute.Sitemap {
  return images.map((image) => {
    const asset = assetUrl(image.path);

    return {
      url: `${SITE_ORIGIN}/images/${image.slug ?? image.id}`,
      lastModified: new Date(image.created_at),
      ...(asset ? { images: [asset] } : {}),
    };
  });
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  try {
    const [categories, components, images] = await Promise.all([
      listCategories(),
      everyComponent(),
      everyImage(),
    ]);

    const blockDates = components.map((component) => component.created_at);
    const imageDates = images.map((image) => image.created_at);

    return [
      {
        url: `${SITE_ORIGIN}/blocks`,
        lastModified: latest(blockDates),
      },
      {
        url: `${SITE_ORIGIN}/images`,
        lastModified: latest(imageDates),
      },
      ...entriesFor(STATIC_PATHS),
      ...categoryEntries(categories, components, images),
      ...componentEntries(components),
      ...imageEntries(images),
    ];
  } catch (error) {
    // A sitemap that answers 500 tells a crawler nothing. The public shell is
    // still worth submitting while the vault is unavailable, and the log keeps
    // the failure visible to the operator.
    const reason =
      error instanceof VaultUnreadable
        ? error.message
        : error instanceof Error
          ? error.message
          : String(error);
    console.error(`sitemap: falling back to static routes (${reason})`);

    return entriesFor([...CATALOGUE_PATHS, ...STATIC_PATHS]);
  }
}
