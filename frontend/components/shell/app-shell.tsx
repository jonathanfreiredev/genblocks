import type { ReactNode } from "react";

import { Breadcrumbs } from "@/components/breadcrumbs";
import { AppHeader } from "@/components/shell/app-header";
import { AppSidebar } from "@/components/shell/app-sidebar";
import { VerificationBanner } from "@/components/auth/verification-banner";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import type { Session } from "@/server/auth/auth.lib";
import type { Category } from "@/lib/vault/types";

/**
 * The shell every signed-in or public page shares.
 *
 * It is the provider and the two pieces of chrome, nothing else. Pages own
 * their content and their headings; the breadcrumb band owns wayfinding; the
 * sidebar owns navigation. Keeping the three apart is what lets the sidebar be
 * a real shadcn sidebar rather than a column of links each page re-draws.
 */
export function AppShell({
  session,
  categories,
  children,
}: {
  session: Session | null;
  categories: Category[];
  children: ReactNode;
}) {
  return (
    <SidebarProvider>
      <AppSidebar categories={categories} signedIn={session !== null} />
      <SidebarInset className="min-h-svh min-w-0">
        <AppHeader session={session} />
        {session && !session.user.isVerified ? <VerificationBanner /> : null}
        <Breadcrumbs categories={categories} />
        <div className="flex min-h-0 flex-1 flex-col">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
