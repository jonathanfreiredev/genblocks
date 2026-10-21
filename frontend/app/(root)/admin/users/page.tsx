import type { Metadata } from "next";
import Link from "next/link";
import { notFound, redirect } from "next/navigation";

import { AdminUserActions } from "@/components/admin/user-actions";
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
import { listAdminUsers } from "@/lib/admin/api";
import { cn } from "@/lib/utils";
import { formatDate } from "@/lib/vault/format";
import { getSession } from "@/server/auth/auth.lib";

export const metadata: Metadata = {
  title: "Users",
  description: "Find a profile and decide whether it may use the product.",
};

export default async function AdminUsersPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const session = await getSession();
  if (!session) {
    redirect("/auth/login?next=%2Fadmin%2Fusers");
  }
  if (!session.user.isAdmin) {
    notFound();
  }

  const params = await searchParams;
  const search = typeof params.search === "string" ? params.search : undefined;
  const users = await listAdminUsers(session.session.token, {
    search,
    limit: 100,
  });

  return (
    <div className="mx-auto flex w-full max-w-[980px] flex-col gap-8 px-6 py-10">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-2">
          <p className="text-muted-foreground text-xs font-medium tracking-[0.05em] uppercase">
            Operate
          </p>
          <h1 className="text-2xl font-semibold tracking-tight">Users</h1>
          <p className="text-muted-foreground max-w-[62ch] text-sm">
            A ban stops an existing token and Supabase refuses the next login.
            The person can still browse public blocks as an anonymous visitor.
          </p>
        </div>
        <Badge variant="outline" className="w-fit tabular-nums">
          {users.length} {users.length === 1 ? "profile" : "profiles"}
        </Badge>
      </header>

      <form className="flex max-w-md gap-2" action="/admin/users">
        <input
          name="search"
          defaultValue={search}
          placeholder="Search email or name"
          className="border-input bg-background h-8 min-w-0 flex-1 rounded-lg border px-2.5 text-sm outline-none focus-visible:ring-3"
        />
        <button className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
          Search
        </button>
      </form>

      {users.length === 0 ? (
        <Empty className="border-border border-t py-16">
          <EmptyHeader>
            <EmptyTitle>No profiles</EmptyTitle>
            <EmptyDescription>
              {search ? "No user matches this search." : "Nobody has signed in yet."}
            </EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ul className="flex flex-col gap-3">
          {users.map((user) => (
            <li key={user.id}>
              <Card>
                <CardHeader className="gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <CardTitle className="text-base">
                      {user.full_name || "Unnamed profile"}
                    </CardTitle>
                    <Badge variant={user.banned_at ? "destructive" : "secondary"}>
                      {user.banned_at ? "banned" : "active"}
                    </Badge>
                  </div>
                  <CardDescription className="flex flex-wrap gap-x-2 gap-y-1">
                    <span>{user.email ?? "no email"}</span>
                    <span aria-hidden>·</span>
                    <span className="font-mono text-xs">{user.id.slice(0, 8)}</span>
                    <span aria-hidden>·</span>
                    <span className="tabular-nums">
                      joined {formatDate(user.created_at)}
                    </span>
                  </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-wrap items-end justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-muted-foreground text-xs">Reason</p>
                    <p className="truncate text-sm">
                      {user.ban_reason ?? "No reason recorded."}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <Link
                      href={`/admin/users/${user.id}`}
                      className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
                    >
                      Open
                    </Link>
                    <AdminUserActions user={user} />
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
