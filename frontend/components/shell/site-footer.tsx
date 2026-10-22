import Link from "next/link";

/**
 * The legal line under every page.
 *
 * It is deliberately quiet: the catalogue is the product, and the footer only
 * has to make the notices reachable without competing with it. The mobile
 * padding leaves room for the floating assistant button.
 */
export function SiteFooter() {
  return (
    <footer className="border-t px-3 pt-5 pb-24 md:px-4 md:pb-5">
      <div className="text-muted-foreground mx-auto flex w-full max-w-6xl flex-col gap-2 text-xs sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} GenBlocks. All rights reserved.</p>
        <nav
          aria-label="Site"
          className="flex flex-wrap items-center gap-x-4 gap-y-2"
        >
          <Link
            href="/about"
            className="hover:text-foreground underline-offset-4 transition-colors hover:underline"
          >
            About
          </Link>
          <Link
            href="/impressum"
            className="hover:text-foreground underline-offset-4 transition-colors hover:underline"
          >
            Impressum
          </Link>
          <Link
            href="/privacy"
            className="hover:text-foreground underline-offset-4 transition-colors hover:underline"
          >
            Privacy
          </Link>
          <Link
            href="/terms"
            className="hover:text-foreground underline-offset-4 transition-colors hover:underline"
          >
            Terms
          </Link>
        </nav>
      </div>
    </footer>
  );
}
