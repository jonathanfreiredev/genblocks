import Link from "next/link";
import { notFound } from "next/navigation";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  ComponentCell,
  ImageCell,
  ItemGrid,
} from "@/components/vault/item-grid";
import { categoryDescription, catalogueIntro } from "@/lib/seo/categories";
import { JsonLd, collectionPageJsonLd } from "@/lib/seo/json-ld";
import {
  PAGE_SIZE,
  SECTION_KIND,
  catalogueHref,
  itemHref,
  offsetFor,
  parseCatalogue,
  type CatalogueView,
  type Section,
} from "@/lib/vault/links";
import {
  VaultUnreadable,
  listCategories,
  listComponents,
  listImages,
} from "@/lib/vault/api";
import type { Category, ComponentSummary, Image } from "@/lib/vault/types";

type SearchParams = Record<string, string | string[] | undefined>;

const NOUN: Record<Section, { one: string; many: string }> = {
  blocks: { one: "block", many: "blocks" },
  images: { one: "image", many: "images" },
};

function Pager({ view, total }: { view: CatalogueView; total: number }) {
  const pages = Math.ceil(total / PAGE_SIZE);

  if (pages <= 1) {
    return null;
  }

  const previous =
    view.page > 1 ? catalogueHref({ ...view, page: view.page - 1 }) : null;
  const next =
    view.page < pages ? catalogueHref({ ...view, page: view.page + 1 }) : null;

  return (
    <nav
      aria-label="Pages"
      className="mt-6 flex items-center justify-between gap-4"
    >
      {previous ? (
        <Link
          href={previous}
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Previous
        </Link>
      ) : (
        <Button variant="outline" size="sm" disabled>
          Previous
        </Button>
      )}

      <p className="text-muted-foreground text-xs tabular-nums">
        Page {view.page} of {pages}
      </p>

      {next ? (
        <Link
          href={next}
          className={buttonVariants({ variant: "outline", size: "sm" })}
        >
          Next
        </Link>
      ) : (
        <Button variant="outline" size="sm" disabled>
          Next
        </Button>
      )}
    </nav>
  );
}

function NothingFiled({
  view,
  noun,
}: {
  view: CatalogueView;
  noun: { one: string; many: string };
}) {
  const filtered = Boolean(view.q || view.type);
  const description = view.q
    ? `Nothing in the ${noun.many} matches “${view.q}”.`
    : view.type
      ? `No ${noun.many} filed under that category yet.`
      : `The ${noun.many} are empty. Nothing has been published so far.`;

  return (
    <Empty className="py-20">
      <EmptyHeader>
        <EmptyTitle>Nothing filed yet</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>
      {filtered ? (
        <EmptyContent>
          <Link
            href={catalogueHref({ section: view.section, page: 1 })}
            className={buttonVariants({ variant: "link" })}
          >
            Clear the filters
          </Link>
        </EmptyContent>
      ) : null}
    </Empty>
  );
}

/**
 * The public wall of one section.
 *
 * The heading is small on purpose: the sidebar says where you are, and the
 * pictures are the argument. It exists because a landing page needs an H1 and
 * a sentence for a reader who arrives from search, not because the wall needs
 * a hero.
 */
export async function CataloguePage({
  section,
  typeSlug,
  searchParams,
}: {
  section: Section;
  typeSlug?: string;
  searchParams: SearchParams;
}) {
  const view = parseCatalogue(section, searchParams, typeSlug);
  const noun = NOUN[section];
  const kind = SECTION_KIND[section];

  let categories: Category[] = [];
  let type: Category | undefined;
  let items: (ComponentSummary | Image)[] = [];
  let total = 0;
  let failure: string | null = null;

  try {
    categories = await listCategories();

    type = typeSlug
      ? categories.find(
          (category) =>
            category.kind === kind &&
            category.level === 2 &&
            category.slug === typeSlug,
        )
      : undefined;

    if (typeSlug && !type) {
      notFound();
    }

    const query = {
      categoryId: type?.id,
      search: view.q,
      limit: PAGE_SIZE,
      offset: offsetFor(view),
    };

    if (section === "images") {
      const page = await listImages(query);
      items = page.items;
      total = page.total;
    } else {
      const page = await listComponents(query);
      items = page.items;
      total = page.total;
    }
  } catch (error) {
    if (!(error instanceof VaultUnreadable)) {
      throw error;
    }

    failure = error.message;
  }

  const heading = type
    ? `${type.name} ${section === "images" ? "images" : "blocks"}`
    : section === "images"
      ? "Stock images"
      : "UI blocks";
  const intro = type
    ? categoryDescription(type.slug, type.name, section)
    : catalogueIntro(section);
  const schemaPath = catalogueHref({ ...view, q: undefined });
  const collectionItems =
    section === "images"
      ? (items as Image[]).map((image) => ({
          name: image.prompt,
          path: itemHref(section, image.slug ?? image.id),
        }))
      : (items as ComponentSummary[]).map((component) => ({
          name: component.title,
          path: itemHref(section, component.slug),
        }));

  return (
    <div className="flex flex-1 flex-col px-3 py-4 md:px-4">
      {!failure ? (
        <JsonLd
          data={collectionPageJsonLd({
            name: heading,
            description: intro,
            path: schemaPath,
            items: collectionItems,
          })}
        />
      ) : null}

      <div className="flex flex-col gap-1 pb-4">
        <h1 className="text-xl font-semibold tracking-tight">{heading}</h1>
        <p className="text-muted-foreground max-w-[72ch] text-sm">{intro}</p>
      </div>

      {failure ? (
        <Alert variant="destructive">
          <AlertTitle>The vault did not answer</AlertTitle>
          <AlertDescription>
            <p>
              Nothing is lost: this page reads the vault on every request.
              Reload to try again.
            </p>
            <p className="mt-2 text-xs">{failure}</p>
          </AlertDescription>
        </Alert>
      ) : (
        <>
          <div className="flex flex-wrap items-baseline justify-between gap-2 pb-3">
            <p className="text-muted-foreground text-sm">
              {total} {total === 1 ? noun.one : noun.many}
              {view.q ? (
                <>
                  {" "}
                  for <span className="text-foreground">“{view.q}”</span>
                </>
              ) : null}
            </p>

            {view.q ? (
              <Link
                href={catalogueHref({
                  section,
                  type: view.type,
                  page: 1,
                })}
                className={buttonVariants({ variant: "link", size: "xs" })}
              >
                Clear search
              </Link>
            ) : null}
          </div>

          {items.length > 0 ? (
            <ItemGrid>
              {section === "images"
                ? (items as Image[]).map((image, index) => (
                    <ImageCell
                      key={image.id}
                      image={image}
                      href={itemHref(section, image.slug ?? image.id)}
                      priority={index < 5}
                    />
                  ))
                : (items as ComponentSummary[]).map((component, index) => (
                    <ComponentCell
                      key={component.id}
                      component={component}
                      href={itemHref(section, component.slug)}
                      priority={index < 5}
                    />
                  ))}
            </ItemGrid>
          ) : (
            <NothingFiled view={view} noun={noun} />
          )}

          <Pager view={view} total={total} />
        </>
      )}
    </div>
  );
}
