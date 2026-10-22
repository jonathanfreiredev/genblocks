import type { Metadata } from "next";

import { SITE_AUTHOR, SITE_LOCALE, SITE_NAME, canonicalPath } from "@/lib/site";

type OpenGraphKind = "website" | "article";

interface PageMetadataOptions {
  title: string;
  description: string;
  /** Canonical path, including a query string when the page is a paginated view. */
  path: string;
  /** Search results and private surfaces stay out of the index. */
  noindex?: boolean;
  type?: OpenGraphKind;
  publishedTime?: string;
  authors?: string[];
  section?: string;
}

/** Collapse whitespace and keep descriptions inside the useful search length. */
export function clampDescription(value: string, limit = 160): string {
  const plain = value.replace(/\s+/g, " ").trim();

  if (plain.length <= limit) {
    return plain;
  }

  const clipped = plain.slice(0, limit - 1);
  const lastSpace = clipped.lastIndexOf(" ");

  return `${(lastSpace > limit * 0.6 ? clipped.slice(0, lastSpace) : clipped).trimEnd()}…`;
}

/**
 * The metadata every public page shares.
 *
 * The file-based Open Graph image in the route segment wins over anything here,
 * so this helper deliberately does not set `images`: a page gets the card that
 * belongs to its segment, and the root card is the fallback.
 */
export function pageMetadata({
  title,
  description,
  path,
  noindex = false,
  type = "website",
  publishedTime,
  authors,
  section,
}: PageMetadataOptions): Metadata {
  const canonical = canonicalPath(path);
  const cleanDescription = clampDescription(description);

  return {
    title,
    description: cleanDescription,
    alternates: { canonical },
    robots: noindex
      ? { index: false, follow: false, noarchive: true }
      : { index: true, follow: true },
    openGraph: {
      type,
      title,
      description: cleanDescription,
      url: canonical,
      siteName: SITE_NAME,
      locale: SITE_LOCALE,
      ...(publishedTime ? { publishedTime } : {}),
      ...(authors && authors.length > 0 ? { authors } : {}),
      ...(section ? { section } : {}),
    },
    twitter: {
      card: "summary_large_image",
      title,
      description: cleanDescription,
    },
    authors: [SITE_AUTHOR],
  };
}

/**
 * A readable title from a prompt.
 *
 * Image prompts are often a paragraph. The metadata needs a phrase a person can
 * scan, while the page keeps the full prompt as its H1 and its description.
 */
export function titleFromPrompt(prompt: string, limit = 72): string {
  const clean = prompt.replace(/\s+/g, " ").trim();
  const firstSentence = clean.match(/^.*?[.!?](?:\s|$)/)?.[0]?.trim() ?? clean;

  return clampDescription(firstSentence, limit);
}
