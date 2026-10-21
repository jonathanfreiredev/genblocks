import type { Category } from "@/lib/vault/types";
import { isUuid, SECTION_KIND, type Section } from "@/lib/vault/links";

export type Crumb = {
  label: string;
  /** Absent on the page the visitor is already reading. */
  href?: string;
};

const SECTION_LABELS: Record<Section, string> = {
  blocks: "Blocks",
  images: "Images",
};

const SEGMENT_LABELS: Record<string, string> = {
  profile: "Profile",
  tasks: "Your tasks",
};

function humanize(segment: string): string {
  return segment
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Turn a pathname into the trail under the header.
 *
 * There is no home page anymore, so the first crumb is the section itself:
 * Blocks, Images, Your tasks. A type is the second crumb and the item pages stop
 * at their section — their own title is the page's h1, and repeating it in the
 * band above would be the same word twice.
 */
export function buildBreadcrumbs(
  pathname: string,
  categories: Category[] = [],
): Crumb[] {
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) {
    return [];
  }

  const [first, second] = segments;

  if (first === "blocks" || first === "images") {
    const section = first as Section;
    const label = SECTION_LABELS[section];

    if (!second) {
      return [{ label }];
    }

    if (isUuid(second)) {
      // An item: the band keeps the way back, and the page's own h1 is the item.
      return [{ label, href: `/${section}` }];
    }

    const kind = SECTION_KIND[section];
    const type = categories.find(
      (category) =>
        category.kind === kind &&
        category.level === 2 &&
        category.slug === second,
    );

    // An item's own h1 is its name; the band only needs the way back. A second
    // segment that is not a type is the item, not a category.
    if (!type) {
      return [{ label, href: `/${section}` }];
    }

    return [{ label, href: `/${section}` }, { label: type.name }];
  }

  if (first === "tasks") {
    if (!second) {
      return [{ label: "Your tasks" }];
    }

    return [
      { label: "Your tasks", href: "/tasks" },
      { label: isUuid(second) ? second.slice(0, 8) : humanize(second) },
    ];
  }

  if (SEGMENT_LABELS[first]) {
    return [{ label: SEGMENT_LABELS[first] }];
  }

  // Anything else is a route this file has not met yet; the URL is still the
  // source of truth, so it gets a readable trail rather than nothing.
  const trail: Crumb[] = [];
  let href = "";

  for (const segment of segments) {
    href += `/${segment}`;
    trail.push({ label: humanize(segment), href });
  }

  return trail;
}
