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
import { getAdminUser } from "@/lib/admin/api";
import { cn } from "@/lib/utils";
import { formatDate, formatTime } from "@/lib/vault/format";
import { getSession } from "@/server/auth/auth.lib";

export const metadata: Metadata = {
  title: "User",
  description: "One profile and the manual ban decision.",
};

export default async function AdminUserPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await getSession();
  const { id } = await params;

  if (!session) {
    redirect(`/auth/login?next=%2Fadmin%2Fusers%2F${id}`);
  }
  if (!session.user.isAdmin) {
    notFound();
  }

  const user = await getAdminUser(session.session.token, id);

  return (
    <div className="mx-auto flex w-full max-w-[760px] flex-col gap-6 px-6 py-10">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex flex-col gap-2">
          <Link
            href="/admin/users"
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
          >
            ← Users
          </Link>
          <h1 className="text-2xl font-semibold tracking-tight">
            {user.full_name || "Unnamed profile"}
          </h1>
          <p className="text-muted-foreground text-sm">{user.email ?? "no email"}</p>
        </div>
        <AdminUserActions user={user} />
      </div>

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="text-base">Account</CardTitle>
            <Badge variant={user.banned_at ? "destructive" : "secondary"}>
              {user.banned_at ? "banned" : "active"}
            </Badge>
          </div>
          <CardDescription>
            A ban blocks this profile and Supabase login. Public browsing remains
            available without signing in.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-muted-foreground text-xs">User id</p>
            <p className="break-all font-mono text-xs">{user.id}</p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Joined</p>
            <p className="text-sm tabular-nums">
              {formatDate(user.created_at)} {formatTime(user.created_at)}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Banned at</p>
            <p className="text-sm tabular-nums">
              {user.banned_at
                ? `${formatDate(user.banned_at)} ${formatTime(user.banned_at)}`
                : "Not banned"}
            </p>
          </div>
          <div>
            <p className="text-muted-foreground text-xs">Reason</p>
            <p className="text-sm">{user.ban_reason ?? "No reason recorded."}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
