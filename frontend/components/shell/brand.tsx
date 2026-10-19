import Image from "next/image";
import Link from "next/link";

import logo from "@/app/icon.png";
import { cn } from "@/lib/utils";

/**
 * The mark and the wordmark, in the one form the shell uses.
 *
 * `compact` is for the collapsed sidebar: the icon stays, the name goes. The
 * icon is the same file the browser uses as a favicon, so the product does not
 * have two marks to keep in sync.
 */
export function Brand({
  compact = false,
  className,
}: {
  compact?: boolean;
  className?: string;
}) {
  return (
    <Link
      href="/blocks"
      className={cn(
        "flex items-center gap-2 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring",
        className,
      )}
    >
      <Image
        src={logo}
        alt=""
        width={24}
        height={24}
        className="size-6 shrink-0 rounded-md"
        priority
      />
      {compact ? null : (
        <span className="truncate text-sm font-semibold tracking-tight">
          GenBlocks
        </span>
      )}
    </Link>
  );
}
