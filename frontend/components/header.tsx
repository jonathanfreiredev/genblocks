import Link from "next/link";
import { HeaderAuthButtons } from "./auth/header-auth-buttons";
import { HeaderBackdrop } from "./header-backdrop";
import { SidebarSheet } from "./sidebar-sheet";
import { DropdownAvatarMenu } from "./dropdown-avatar-menu";
import { Session } from "@/server/auth/auth.lib";

interface HeaderProps {
  session: Session | null;
}

export async function Header({ session }: HeaderProps) {
  return (
    <header className="fixed z-1 h-24 w-full px-6">
      <HeaderBackdrop />

      <div className="flex h-full w-full items-center justify-between">
        <Link href="/" passHref className="flex h-full items-center">
          {/* A wordmark, not a heading: each page owns its single h1. */}
          <span className="relative font-semibold text-gray-800">
            MCPStack
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <div className="hidden sm:flex">
            {!!session ? (
              <DropdownAvatarMenu user={{ name: session.user.name }} />
            ) : (
              <HeaderAuthButtons />
            )}
          </div>

          <div className="flex sm:hidden">
            <SidebarSheet isLoggedIn={!!session} />
          </div>
        </div>
      </div>
    </header>
  );
}
