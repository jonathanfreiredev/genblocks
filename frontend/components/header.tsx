import Link from "next/link";
import { HeaderAuthButtons } from "./auth/header-auth-buttons";
import { SidebarSheet } from "./sidebar-sheet";
import { DropdownAvatarMenu } from "./dropdown-avatar-menu";
import { Session } from "@/server/auth/auth.lib";

interface HeaderProps {
  session: Session | null;
}

/**
 * The chrome: a paper band with a hairline under it.
 *
 * Nothing is translucent and nothing blurs — a header that let the sheet show
 * through would be a second surface competing with the one being read. The
 * navigation proper lives on the page (see the vault's rail), because it belongs
 * to what is on screen, not to every screen.
 */
export async function Header({ session }: HeaderProps) {
  return (
    <header className="border-rule bg-background fixed z-1 h-24 w-full border-b px-6">
      <div className="flex h-full w-full items-center justify-between">
        <Link href="/" passHref className="flex h-full items-center">
          {/* A wordmark, not a heading: each page owns its single h1. */}
          <span className="text-ink relative font-semibold">GenBlocks</span>
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
