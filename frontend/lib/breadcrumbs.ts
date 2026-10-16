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

function humanize(segment: string): string {
  return segment
    .split("-")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Turn a pathname into the trail of breadcrumbs shown under the header.
 *
 * The first crumb is always the home page, so there is a way back from any
 * nested page. The home page itself returns an empty trail: there is nothing to
 * trail back to, and callers use that to hide the breadcrumb.
 *
 * Note: dynamic segments (`[id]`) come out as their literal name; add them to
 * `SEGMENT_LABELS` when you introduce one.
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
    trail.push({ label: SEGMENT_LABELS[segment] ?? humanize(segment), href });
  }

  return trail;
}
