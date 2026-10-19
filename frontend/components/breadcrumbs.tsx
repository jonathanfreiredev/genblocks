"use client";

import { Fragment } from "react";
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
import type { Category } from "@/lib/vault/types";

/**
 * The muted band under the header.
 *
 * It is the only place the taxonomy is named outside the sidebar, so it answers
 * "where am I" without competing with the page. On an item page it stops at the
 * section: the h1 right below already says the item's name.
 */
export function Breadcrumbs({ categories }: { categories: Category[] }) {
  const pathname = usePathname();
  const trail = buildBreadcrumbs(pathname, categories);

  if (trail.length === 0) {
    return null;
  }

  return (
    <div className="bg-muted/40 border-b">
      <Breadcrumb className="px-3 py-2 md:px-4">
        <BreadcrumbList>
          {trail.map((crumb, index) => {
            const isCurrent = index === trail.length - 1;

            return (
              <Fragment key={`${crumb.label}-${index}`}>
                <BreadcrumbItem>
                  {isCurrent || !crumb.href ? (
                    <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink href={crumb.href}>
                      {crumb.label}
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
                {!isCurrent ? <BreadcrumbSeparator /> : null}
              </Fragment>
            );
          })}
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  );
}
