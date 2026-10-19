import Link from "next/link";
import { notFound } from "next/navigation";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
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
        <Button variant="outline" size="sm" render={<Link href={previous} />}>
          Previous
        </Button>
      ) : (
        <Button variant="outline" size="sm" disabled>
          Previous
        </Button>
      )}

      <p className="text-muted-foreground text-xs tabular-nums">
        Page {view.page} of {pages}
      </p>

      {next ? (
        <Button variant="outline" size="sm" render={<Link href={next} />}>
          Next
        </Button>
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
          <Button
            variant="link"
            render={
              <Link href={catalogueHref({ section: view.section, page: 1 })} />
            }
          >
            Clear the filters
          </Button>
        </EmptyContent>
      ) : null}
    </Empty>
  );
}

/**
 * The public wall of one section.
 *
 * No hero, no description, no oversized section title: the sidebar says where
 * you are and the pictures are the argument. The only text above the grid is
 * the count, and the only text on a cell appears when the pointer asks for the
 * maker's name.
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
  let items: (ComponentSummary | Image)[] = [];
  let total = 0;
  let failure: string | null = null;

  try {
    categories = await listCategories();

    const type = typeSlug
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

  return (
    <div className="flex flex-1 flex-col px-3 py-4 md:px-4">
      <h1 className="sr-only">{section === "images" ? "Images" : "Blocks"}</h1>

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
              <Button
                variant="link"
                size="xs"
                render={
                  <Link
                    href={catalogueHref({
                      section,
                      type: view.type,
                      page: 1,
                    })}
                  />
                }
              >
                Clear search
              </Button>
            ) : null}
          </div>

          {items.length > 0 ? (
            <ItemGrid>
              {section === "images"
                ? (items as Image[]).map((image) => (
                    <ImageCell
                      key={image.id}
                      image={image}
                      href={itemHref(section, image.id)}
                    />
                  ))
                : (items as ComponentSummary[]).map((component) => (
                    <ComponentCell
                      key={component.id}
                      component={component}
                      href={itemHref(section, component.id)}
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
