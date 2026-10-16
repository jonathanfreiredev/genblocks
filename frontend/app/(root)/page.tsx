import type { Metadata } from "next";
import Link from "next/link";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyContent,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import { Input } from "@/components/ui/input";
import {
  ComponentCell,
  ImageCell,
  ItemGrid,
} from "@/components/vault/item-grid";
import { ComponentDialog, ImageDialog } from "@/components/vault/item-dialog";
import { VaultRail } from "@/components/vault/vault-rail";
import { cn } from "@/lib/utils";
import {
  VaultUnreadable,
  getComponent,
  getImage,
  listCategories,
  listComponentGenerations,
  listComponents,
  listImages,
} from "@/lib/vault/api";
import {
  PAGE_SIZE,
  catalogueHref,
  itemHref,
  offsetFor,
  parseCatalogue,
  type CatalogueRequest,
  type CatalogueView,
} from "@/lib/vault/links";
import type {
  Category,
  Component,
  ComponentSummary,
  Generation,
  Image,
  Kind,
} from "@/lib/vault/types";

export const metadata: Metadata = {
  title: "The vault",
  description:
    "Blocks and stock images generated from a prompt, each carrying the scores an independent judge gave it and the attempts that came before it.",
};

type SearchParams = Record<string, string | string[] | undefined>;

type Catalogue =
  | { kind: "component"; items: ComponentSummary[]; total: number }
  | { kind: "image"; items: Image[]; total: number };

type Opened =
  | { kind: "component"; component: Component; generations: Generation[] }
  | { kind: "image"; image: Image };

const COPY: Record<
  Kind,
  { h1: string; lead: string; noun: string; placeholder: string }
> = {
  component: {
    h1: "Blocks",
    lead: "Every block here was generated from a brief and scored by a judge that did not write it. Open one to read its code, the brief it came from, and the attempts that came before it.",
    noun: "blocks",
    placeholder: "Search the blocks",
  },
  image: {
    h1: "Images",
    lead: "Stock images generated from a prompt and scored before they entered the library. Each row keeps the recipe it was made from.",
    noun: "images",
    placeholder: "Search the prompts",
  },
};

async function loadOpened(request: CatalogueRequest): Promise<Opened | null> {
  const id = request.item;

  if (!id) {
    return null;
  }

  if (request.kind === "image") {
    const image = await getImage(id);

    return image ? { kind: "image", image } : null;
  }

  const component = await getComponent(id);

  if (!component) {
    return null;
  }

  return {
    kind: "component",
    component,
    generations: await listComponentGenerations(component.id),
  };
}

function categoryName(categories: Category[], id: string): string {
  return categories.find((category) => category.id === id)?.name ?? "Unfiled";
}

/** One page of the sheet, walked with two links rather than a control. */
function Pager({ view, total }: { view: CatalogueView; total: number }) {
  const pages = Math.ceil(total / PAGE_SIZE);

  if (pages <= 1) {
    return null;
  }

  return (
    <nav
      aria-label="Pages"
      className="border-rule flex items-baseline justify-between gap-4 border-t pt-4"
    >
      <PageLink
        href={
          view.page > 1 ? catalogueHref({ ...view, page: view.page - 1 }) : null
        }
        label="Previous"
      />

      <p className="type-meta text-ink-faint tabular-nums">
        Page {view.page} of {pages}
      </p>

      <PageLink
        href={
          view.page < pages
            ? catalogueHref({ ...view, page: view.page + 1 })
            : null
        }
        label="Next"
        align="right"
      />
    </nav>
  );
}

function PageLink({
  href,
  label,
  align,
}: {
  href: string | null;
  label: string;
  align?: "right";
}) {
  const styles = cn("type-label", align === "right" && "text-right");

  if (!href) {
    return <span className={cn(styles, "text-rule-strong")}>{label}</span>;
  }

  return (
    <Link
      href={href}
      className={cn(styles, "text-ink underline-offset-4 hover:underline")}
    >
      {label}
    </Link>
  );
}

function NothingFiled({
  request,
  typeName,
  noun,
}: {
  request: CatalogueRequest;
  typeName?: string;
  noun: string;
}) {
  const description = request.q
    ? `Nothing in the ${noun} matches “${request.q}”.`
    : request.type && typeName
      ? `No ${noun} filed under ${typeName} yet.`
      : `The ${noun} are empty. Nothing has been published so far.`;

  const filtered = Boolean(request.q || request.type);

  return (
    <Empty className="py-20">
      <EmptyHeader>
        <EmptyTitle className="type-title">Nothing filed yet</EmptyTitle>
        <EmptyDescription>{description}</EmptyDescription>
      </EmptyHeader>

      {filtered ? (
        <EmptyContent>
          <Button
            variant="link"
            render={
              <Link href={catalogueHref({ kind: request.kind, page: 1 })} />
            }
          >
            Clear the filters
          </Button>
        </EmptyContent>
      ) : null}
    </Empty>
  );
}

function VaultFailure({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertTitle>The vault did not answer</AlertTitle>
      <AlertDescription>
        <p>
          Nothing is lost: this page reads the vault on every request. Reload to
          try again.
        </p>
        <p className="type-meta mt-2">{message}</p>
      </AlertDescription>
    </Alert>
  );
}

/**
 * The public face: the sheet of everything the vault holds.
 *
 * It is a gallery rather than a landing page because the items are the argument
 * — each one arrives with the scores of a judge that did not write it. The
 * address carries the whole view, so a filter, a page and an open item can all
 * be linked to, and the browser's Back does what it says.
 */
export default async function VaultPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const request = parseCatalogue(await searchParams);
  const copy = COPY[request.kind];

  let categories: Category[] = [];
  let catalogue: Catalogue | null = null;
  let opened: Opened | null = null;
  let failure: string | null = null;

  try {
    categories = await listCategories();

    const categoryId = categories.find(
      (category) =>
        category.kind === request.kind && category.slug === request.type,
    )?.id;

    const query = {
      categoryId,
      search: request.q,
      limit: PAGE_SIZE,
      offset: offsetFor(request),
    };

    if (request.kind === "image") {
      const page = await listImages(query);
      catalogue = { kind: "image", items: page.items, total: page.total };
    } else {
      const page = await listComponents(query);
      catalogue = { kind: "component", items: page.items, total: page.total };
    }

    opened = await loadOpened(request);
  } catch (error) {
    if (!(error instanceof VaultUnreadable)) {
      throw error;
    }

    failure = error.message;
  }

  const types = categories.filter(
    (category) => category.kind === request.kind && category.level === 2,
  );
  const typeName = request.type
    ? types.find((type) => type.slug === request.type)?.name
    : undefined;
  const closeHref = catalogueHref(request);

  const dialog =
    opened?.kind === "component" ? (
      <ComponentDialog
        component={opened.component}
        generations={opened.generations}
        typeName={categoryName(categories, opened.component.category_id)}
        closeHref={closeHref}
      />
    ) : opened?.kind === "image" ? (
      <ImageDialog
        image={opened.image}
        typeName={categoryName(categories, opened.image.category_id)}
        closeHref={closeHref}
      />
    ) : null;

  return (
    <div className="mx-auto w-full max-w-[1280px] px-6 pt-[calc(var(--header-height)+2.5rem)] pb-24">
      <div className="grid gap-10 lg:grid-cols-[13rem_minmax(0,1fr)] lg:gap-12">
        <VaultRail view={request} types={types} />

        <div className="flex min-w-0 flex-col gap-8">
          <header className="flex flex-col gap-6">
            <div className="flex flex-col gap-3">
              <h1 className="type-display">{copy.h1}</h1>
              <p className="type-body text-ink-soft max-w-[68ch]">
                {copy.lead}
              </p>
            </div>

            <form action="/" role="search" className="flex items-end gap-3">
              <input type="hidden" name="kind" value={request.kind} />
              {request.type ? (
                <input type="hidden" name="type" value={request.type} />
              ) : null}

              <div className="flex w-full max-w-sm flex-col gap-1.5">
                <label htmlFor="q" className="type-label text-ink-faint">
                  Search
                </label>
                <Input
                  id="q"
                  name="q"
                  defaultValue={request.q}
                  placeholder={copy.placeholder}
                  className="bg-panel"
                />
              </div>

              <Button type="submit" variant="secondary">
                Search
              </Button>
            </form>
          </header>

          {failure ? <VaultFailure message={failure} /> : null}

          {!failure && catalogue ? (
            <div className="flex flex-col gap-6">
              <p className="type-label border-rule text-ink-faint border-b pb-3">
                {catalogue.total} {copy.noun}
              </p>

              {catalogue.items.length > 0 ? (
                <ItemGrid>
                  {catalogue.kind === "component"
                    ? catalogue.items.map((component, index) => (
                        <ComponentCell
                          key={component.id}
                          component={component}
                          typeName={categoryName(
                            categories,
                            component.category_id,
                          )}
                          position={offsetFor(request) + index + 1}
                          href={itemHref(request, component.id)}
                        />
                      ))
                    : catalogue.items.map((image, index) => (
                        <ImageCell
                          key={image.id}
                          image={image}
                          typeName={categoryName(categories, image.category_id)}
                          position={offsetFor(request) + index + 1}
                          href={itemHref(request, image.id)}
                        />
                      ))}
                </ItemGrid>
              ) : (
                <NothingFiled
                  request={request}
                  typeName={typeName}
                  noun={copy.noun}
                />
              )}

              <Pager view={request} total={catalogue.total} />
            </div>
          ) : null}
        </div>
      </div>

      {dialog}
    </div>
  );
}
