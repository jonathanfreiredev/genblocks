import { SITE_AUTHOR, SITE_NAME, SITE_ORIGIN, absoluteUrl } from "@/lib/site";
import { assetUrl } from "@/lib/vault/asset";
import type { Component, Image } from "@/lib/vault/types";

const WEBSITE_ID = `${SITE_ORIGIN}/#website`;
const ORGANIZATION_ID = `${SITE_ORIGIN}/#organization`;

type JsonLdData = Record<string, unknown>;

/**
 * JSON-LD is serialized into a script tag. A prompt can contain `</script>`,
 * so escaping the three characters that can end the element is not optional.
 */
export function serializeJsonLd(data: JsonLdData): string {
  return JSON.stringify(data).replace(/[<>&\u2028\u2029]/g, (character) => {
    switch (character) {
      case "<":
        return "\\u003c";
      case ">":
        return "\\u003e";
      case "&":
        return "\\u0026";
      case "\u2028":
        return "\\u2028";
      default:
        return "\\u2029";
    }
  });
}

export function JsonLd({ data }: { data: JsonLdData }) {
  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: serializeJsonLd(data) }}
    />
  );
}

function publisherNode() {
  return { "@id": ORGANIZATION_ID };
}

function authorNode(name: string | null) {
  return name
    ? { "@type": "Person", name }
    : { "@type": "Organization", name: SITE_NAME, url: SITE_ORIGIN };
}

function licenseUrl(license: string): string {
  return /^mit$/i.test(license)
    ? "https://opensource.org/license/mit"
    : license;
}

function imageUrl(path: string | null): string | undefined {
  return path ? (assetUrl(path) ?? undefined) : undefined;
}

export function websiteJsonLd(): JsonLdData {
  return {
    "@type": "WebSite",
    "@id": WEBSITE_ID,
    url: SITE_ORIGIN,
    name: SITE_NAME,
    description:
      "A public registry of generated UI blocks and stock images, each scored by an independent judge.",
    inLanguage: "en",
    publisher: publisherNode(),
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${SITE_ORIGIN}/blocks?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };
}

export function organizationJsonLd(): JsonLdData {
  return {
    "@type": "Organization",
    "@id": ORGANIZATION_ID,
    name: SITE_NAME,
    url: SITE_ORIGIN,
    logo: {
      "@type": "ImageObject",
      url: absoluteUrl("/icon.png"),
      width: 512,
      height: 512,
    },
    founder: {
      "@type": "Person",
      name: SITE_AUTHOR.name,
      url: SITE_AUTHOR.url,
    },
    sameAs: [SITE_AUTHOR.url],
  };
}

export function siteJsonLd(): JsonLdData {
  return {
    "@context": "https://schema.org",
    "@graph": [websiteJsonLd(), organizationJsonLd()],
  };
}

export function webPageJsonLd({
  name,
  description,
  path,
}: {
  name: string;
  description: string;
  path: string;
}): JsonLdData {
  return {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "@id": `${absoluteUrl(path)}#webpage`,
    url: absoluteUrl(path),
    name,
    description,
    inLanguage: "en",
    isPartOf: { "@id": WEBSITE_ID },
    about: publisherNode(),
  };
}

export function aboutPageJsonLd({
  name,
  description,
}: {
  name: string;
  description: string;
}): JsonLdData {
  return {
    "@context": "https://schema.org",
    "@type": "AboutPage",
    "@id": `${absoluteUrl("/about")}#webpage`,
    url: absoluteUrl("/about"),
    name,
    description,
    inLanguage: "en",
    isPartOf: { "@id": WEBSITE_ID },
    mainEntity: {
      "@type": "Organization",
      "@id": ORGANIZATION_ID,
      name: SITE_NAME,
      url: SITE_ORIGIN,
    },
  };
}

export function collectionPageJsonLd({
  name,
  description,
  path,
  items,
}: {
  name: string;
  description: string;
  path: string;
  items: { name: string; path: string }[];
}): JsonLdData {
  return {
    "@context": "https://schema.org",
    "@type": "CollectionPage",
    "@id": `${absoluteUrl(path)}#collection`,
    url: absoluteUrl(path),
    name,
    description,
    inLanguage: "en",
    isPartOf: { "@id": WEBSITE_ID },
    mainEntity: {
      "@type": "ItemList",
      numberOfItems: items.length,
      itemListElement: items.map((item, index) => ({
        "@type": "ListItem",
        position: index + 1,
        name: item.name,
        url: absoluteUrl(item.path),
      })),
    },
  };
}

export function breadcrumbJsonLd(
  items: { name: string; path?: string }[],
): JsonLdData {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      ...(item.path ? { item: absoluteUrl(item.path) } : {}),
    })),
  };
}

export function softwareSourceCodeJsonLd(
  component: Component,
  categoryName: string,
): JsonLdData {
  const files = Object.keys(component.files ?? {});
  const programmingLanguage = files.some((file) =>
    /\.(tsx?|mts|cts)$/.test(file),
  )
    ? "TypeScript"
    : "JavaScript";

  return {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    "@id": `${absoluteUrl(`/blocks/${component.slug}`)}#source`,
    name: component.title,
    description: component.description,
    url: absoluteUrl(`/blocks/${component.slug}`),
    image: imageUrl(component.thumbnail_path ?? component.screenshot_path),
    dateCreated: component.created_at,
    datePublished: component.created_at,
    author: authorNode(component.author),
    publisher: publisherNode(),
    license: licenseUrl(component.license),
    programmingLanguage,
    runtimePlatform: "React",
    creativeWorkStatus: "Published",
    keywords: [categoryName, "UI block", "React", "generated design"],
    isPartOf: { "@id": WEBSITE_ID },
    codeSampleType: "full",
    ...(component.dependencies
      ? { softwareRequirements: Object.keys(component.dependencies) }
      : {}),
  };
}

export function imageObjectJsonLd(
  image: Image,
  categoryName: string,
): JsonLdData {
  const contentUrl = assetUrl(image.path);

  return {
    "@context": "https://schema.org",
    "@type": "ImageObject",
    "@id": `${absoluteUrl(`/images/${image.slug ?? image.id}`)}#image`,
    url: absoluteUrl(`/images/${image.slug ?? image.id}`),
    ...(contentUrl ? { contentUrl, thumbnailUrl: contentUrl } : {}),
    name: image.prompt,
    caption: image.prompt,
    description: image.prompt,
    width: {
      "@type": "QuantitativeValue",
      value: image.width,
      unitCode: "E37",
    },
    height: {
      "@type": "QuantitativeValue",
      value: image.height,
      unitCode: "E37",
    },
    datePublished: image.created_at,
    creator: authorNode(image.author),
    publisher: publisherNode(),
    creditText: image.author ?? SITE_NAME,
    copyrightNotice: `© ${new Date(image.created_at).getUTCFullYear()} ${
      image.author ?? SITE_NAME
    }`,
    license: licenseUrl(image.license),
    keywords: [categoryName, "AI-generated image", "stock image"],
    representativeOfPage: true,
    isPartOf: { "@id": WEBSITE_ID },
  };
}
