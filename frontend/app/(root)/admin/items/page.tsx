import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { AdminItemActions } from "@/components/admin/item-actions";
import { AssetPlate } from "@/components/vault/asset-plate";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyTitle,
} from "@/components/ui/empty";
import {
  asAdminItem,
  listAdminComponents,
  listAdminDeletions,
  listAdminImages,
} from "@/lib/admin/api";
import type { AdminItem } from "@/lib/admin/types";
import { cn } from "@/lib/utils";
import { formatDate, formatTime } from "@/lib/vault/format";
import { getSession } from "@/server/auth/auth.lib";

export const metadata: Metadata = {
  title: "Items",
  description: "Inspect and remove blocks and public image assets.",
};

const LIMIT = 100;

type Kind = "component" | "image";

function kindFrom(value: string | string[] | undefined): Kind {
  return value === "image" ? "image" : "component";
}

export default async function AdminItemsPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const session = await getSession();

  if (!session) {
    redirect("/auth/login?next=%2Fadmin%2Fitems");
  }
  if (!session.user.isAdmin) {
    notFound();
  }

  const params = await searchParams;
  const kind = kindFrom(params.kind);
  const search = typeof params.search === "string" ? params.search : undefined;

  const components =
    kind === "component"
      ? await listAdminComponents(session.session.token, {
          search,
          limit: LIMIT,
        })
      : null;
  const images =
    kind === "image"
      ? await listAdminImages(session.session.token, {
          search,
          limit: LIMIT,
        })
      : null;
  const deletions = await listAdminDeletions(session.session.token, 10);

  const items: AdminItem[] = components
    ? components.items.map((item) => asAdminItem("component", item))
    : (images?.items ?? []).map((item) => asAdminItem("image", item));

  return (
    <div className="mx-auto flex w-full max-w-[1100px] flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-2">
          <p className="text-muted-foreground text-xs font-medium tracking-[0.05em] uppercase">
            Operate
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">Items</h1>
          <p className="text-muted-foreground max-w-[62ch] text-sm">
            Every block and image is public after moderation. Delete one here if
            it should not stay; the row, its Cloudinary asset and its search
            vector are removed permanently.
          </p>
        </div>
        <Badge variant="outline" className="w-fit tabular-nums">
          {components?.total ?? images?.total ?? 0}{" "}
          {(components?.total ?? images?.total ?? 0) === 1 ? "item" : "items"}
        </Badge>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <nav aria-label="Item kind" className="flex flex-wrap gap-2">
          {(
            [
              ["component", "Blocks"],
              ["image", "Images"],
            ] as const
          ).map(([value, label]) => (
            <Link
              key={value}
              href={`/admin/items?kind=${value}`}
              className={cn(
                buttonVariants({
                  variant: kind === value ? "secondary" : "ghost",
                  size: "sm",
                }),
              )}
              aria-current={kind === value ? "page" : undefined}
            >
              {label}
            </Link>
          ))}
        </nav>

        <form className="flex min-w-0 flex-1 gap-2 sm:max-w-sm" action="/admin/items">
          <input type="hidden" name="kind" value={kind} />
          <input
            name="search"
            defaultValue={search}
            placeholder="Search title or prompt"
            className="border-input bg-background h-8 min-w-0 flex-1 rounded-lg border px-2.5 text-sm outline-none focus-visible:ring-3"
          />
          <button className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
            Search
          </button>
        </form>
      </div>

      {items.length === 0 ? (
        <Empty className="border-border border-t py-16">
          <EmptyHeader>
            <EmptyTitle>Nothing here</EmptyTitle>
            <EmptyDescription>
              {search ? "No items match this search." : "This section is empty."}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ul className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <li key={`${item.kind}-${item.id}`}>
              <Card className="flex h-full flex-col overflow-hidden">
                <div className="bg-muted relative aspect-[4/3] w-full overflow-hidden">
                  <AssetPlate
                    path={item.path ?? ""}
                    alt={item.title}
                    sizes="(max-width: 640px) 100vw, 33vw"
                    caption={item.kind === "image" ? "Image preview" : "Block render"}
                  />
                </div>
                <CardHeader>
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline">{item.kind}</Badge>
                  </div>
                  <CardTitle className="line-clamp-2 text-base">
                    {item.title}
                  </CardTitle>
                  <CardDescription className="flex flex-wrap gap-x-2 gap-y-1">
                    <span>{item.author ?? "House"}</span>
                    <span aria-hidden>·</span>
                    <span className="tabular-nums">
                      {formatDate(item.created_at)} {formatTime(item.created_at)}
                    </span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="mt-auto flex flex-col gap-3">
                  <p className="text-muted-foreground truncate font-mono text-xs">
                    {item.slug}
                  </p>
                  <AdminItemActions item={item} />
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}

      <section className="flex flex-col gap-3">
        <div className="flex items-end justify-between gap-4">
          <h2 className="text-lg font-semibold tracking-tight">Recently deleted</h2>
          <p className="text-muted-foreground text-xs">Latest 10 deletions</p>
        </div>

        {deletions.length === 0 ? (
          <p className="text-muted-foreground border-border border-t py-6 text-sm">
            No deletions recorded yet.
          </p>
        ) : (
          <div className="border-border overflow-x-auto border-t">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="text-muted-foreground">
                <tr>
                  <th className="py-2 pr-4 font-medium">Item</th>
                  <th className="py-2 pr-4 font-medium">Kind</th>
                  <th className="py-2 pr-4 font-medium">Actor</th>
                  <th className="py-2 pr-4 font-medium">Result</th>
                  <th className="py-2 font-medium">When</th>
                </tr>
              </thead>
              <tbody>
                {deletions.map((entry) => (
                  <tr key={entry.id} className="border-border border-t">
                    <td className="max-w-[280px] py-2 pr-4">
                      <span className="block truncate">{entry.title}</span>
                      <span className="text-muted-foreground block truncate font-mono text-xs">
                        {entry.slug}
                      </span>
                    </td>
                    <td className="py-2 pr-4">{entry.kind}</td>
                    <td className="py-2 pr-4">{entry.actor ?? "Unknown"}</td>
                    <td className="py-2 pr-4">
                      <Badge variant={entry.result === "deleted" ? "secondary" : "destructive"}>
                        {entry.result}
                      </Badge>
                    </td>
                    <td className="py-2 tabular-nums">
                      {formatDate(entry.created_at)} {formatTime(entry.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
