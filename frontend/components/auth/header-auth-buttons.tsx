"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { buttonVariants } from "../ui/button";

/**
 * Logged-out calls to action for the header. Each button is hidden on the page
 * it points to, so the header never duplicates the form already on screen.
 *
 * Neither is the primary button: the header belongs to every page, and each page
 * owns its own one primary action. A magenta Sign up in the chrome would compete
 * with whatever the page is actually for.
 */
export function HeaderAuthButtons() {
  const pathname = usePathname();

  const showLogin = pathname !== "/auth/login";
  const showSignup = pathname !== "/auth/signup";

  return (
    <div className="flex items-center gap-2">
      {showLogin ? (
        <Link
          href="/auth/login"
          className={buttonVariants({ variant: "outline", size: "lg" })}
        >
          Log in
        </Link>
      ) : null}

      {showSignup ? (
        <Link
          href="/auth/signup"
          className={buttonVariants({ variant: "secondary", size: "lg" })}
        >
          Sign up
        </Link>
      ) : null}
    </div>
  );
}
