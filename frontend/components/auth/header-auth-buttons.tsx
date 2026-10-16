"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { buttonVariants } from "../ui/button";

/**
 * Logged-out calls to action for the header. Each button is hidden on the page
 * it points to, so the header never duplicates the form already on screen.
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
          className={buttonVariants({ variant: "default", size: "lg" })}
        >
          Sign up
        </Link>
      ) : null}
    </div>
  );
}
