"use client";

import { useEffect, useState } from "react";

import { cn } from "@/lib/utils";

/**
 * Backdrop for the fixed header.
 *
 * It only appears once the page is scrolled, so the hero's gradient shows
 * through at the top (nothing gets cut off) while content never bleeds behind
 * the logo on the way down.
 */
export function HeaderBackdrop() {
  const [isScrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);

    // Covers a restored scroll position on reload.
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute inset-0 -z-10 border-b transition-colors duration-200",
        isScrolled
          ? "bg-background/80 border-border/60 backdrop-blur-md"
          : "border-transparent",
      )}
    />
  );
}
