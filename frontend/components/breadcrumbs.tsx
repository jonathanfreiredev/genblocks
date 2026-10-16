"use client";

import { Fragment } from "react";
import { House } from "lucide-react";
import { usePathname } from "next/navigation";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { buildBreadcrumbs } from "@/lib/breadcrumbs";

/**
 * Wayfinding bar sitting directly under the header.
 *
 * It gets its own bordered band so it reads as chrome and never competes with
 * the page's own typography. The trail is derived from the current path, so a
 * new route gets a breadcrumb without any wiring, and it is hidden on the home
 * page, where there is nothing to trail back to.
 */
export function Breadcrumbs() {
  const pathname = usePathname();
  const trail = buildBreadcrumbs(pathname);

  if (trail.length <= 1) {
    return null;
  }

  return (
    <div className="pt-[var(--header-height)]">
      <Breadcrumb className="bg-muted/40 w-full">
        <BreadcrumbList className="w-full px-6 py-2.5">
          {trail.map((crumb, index) => {
            const isCurrentPage = index === trail.length - 1;
            const isHome = crumb.href === "/";

            return (
              <Fragment key={crumb.href}>
                <BreadcrumbItem>
                  {isCurrentPage ? (
                    <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink href={crumb.href}>
                      {isHome ? (
                        <>
                          <House className="size-3.5" aria-hidden="true" />
                          <span className="sr-only">Home</span>
                        </>
                      ) : (
                        crumb.label
                      )}
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
                {!isCurrentPage ? <BreadcrumbSeparator /> : null}
              </Fragment>
            );
          })}
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  );
}
