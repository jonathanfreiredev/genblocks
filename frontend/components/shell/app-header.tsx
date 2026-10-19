"use client";

import { MenuIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { HeaderAuthButtons } from "@/components/auth/header-auth-buttons";
import { DropdownAvatarMenu } from "@/components/dropdown-avatar-menu";
import { Brand } from "@/components/shell/brand";
import { SearchDialog } from "@/components/shell/search-dialog";
import { Button, buttonVariants } from "@/components/ui/button";
import { useSidebar } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";
import { sectionFromPath } from "@/lib/vault/links";

/**
 * The thin band above the page.
 *
 * On a laptop it starts where the sidebar ends and carries search and the
 * account. On a phone it spans the whole width and carries the way into the
 * navigation, the mark, and the account — the mark is centered on its own, so
 * the two controls on the sides cannot push it off the middle.
 */
export function AppHeader({
  session,
}: {
  session: { user: { name: string } } | null;
}) {
  const pathname = usePathname();
  const section = sectionFromPath(pathname);
  const { toggleSidebar } = useSidebar();

  return (
    <header className="sticky top-0 z-30 flex h-[var(--header-height)] shrink-0 items-center gap-2 border-b bg-background/80 px-3 backdrop-blur supports-[backdrop-filter]:bg-background/70 md:px-4">
      <Button
        type="button"
        variant="ghost"
        size="icon-sm"
        className="md:hidden"
        onClick={toggleSidebar}
        aria-label="Open the navigation"
      >
        <MenuIcon />
      </Button>

      <div className="pointer-events-none absolute inset-x-0 flex justify-center md:hidden">
        <div className="pointer-events-auto">
          <Brand />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-1 md:gap-2">
        <SearchDialog section={section} />

        {session ? (
          <DropdownAvatarMenu user={{ name: session.user.name }} />
        ) : (
          <>
            <Link
              href="/auth/login"
              className={cn(
                buttonVariants({ variant: "ghost", size: "sm" }),
                "md:hidden",
              )}
            >
              Log in
            </Link>
            <div className="hidden md:block">
              <HeaderAuthButtons />
            </div>
          </>
        )}
      </div>
    </header>
  );
}
