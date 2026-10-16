export type Breadcrumb = {
  label: string;
  href: string;
};

/**
 * Labels for segments that do not read well when humanised. Everything else is
 * derived from the URL, so a new route gets a breadcrumb without any wiring.
 */
const SEGMENT_LABELS: Record<string, string> = {
  profile: "Profile",
};

/** A uuid as it appears in a URL. */
const UUID_SEGMENT =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function humanize(segment: string): string {
  return segment
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * The readable label for one segment.
 *
 * A resource addressed by its id (a task, an item) has no name of its own in
 * the URL, and humanising thirty-six hex characters gives a crumb that pushes
 * everything else off a phone. The first eight characters are enough to tell two
 * of them apart and short enough to sit in a trail.
 */
function segmentLabel(segment: string): string {
  if (SEGMENT_LABELS[segment]) {
    return SEGMENT_LABELS[segment];
  }

  return UUID_SEGMENT.test(segment) ? segment.slice(0, 8) : humanize(segment);
}

/**
 * Turn a pathname into the trail of breadcrumbs shown under the header.
 *
 * The first crumb is always the home page, so there is a way back from any
 * nested page. The home page itself returns an empty trail: there is nothing to
 * trail back to, and callers use that to hide the breadcrumb.
 *
 * Note: dynamic segments (`[id]`) come out as their literal name; add them to
 * `SEGMENT_LABELS` when they are a word, or leave them to the short-id rule when
 * they are an id.
 */
export function buildBreadcrumbs(pathname: string): Breadcrumb[] {
  const segments = pathname.split("/").filter(Boolean);

  if (segments.length === 0) {
    return [];
  }

  const trail: Breadcrumb[] = [{ label: "Home", href: "/" }];
  let href = "";

  for (const segment of segments) {
    href += `/${segment}`;
    trail.push({ label: segmentLabel(segment), href });
  }

  return trail;
}
