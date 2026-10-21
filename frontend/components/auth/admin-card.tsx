import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export function AdminCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Operator tools</CardTitle>
        <CardDescription>
          Inspect the public vault, remove anything that should not stay, and
          decide who may use the product.
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Link href="/admin/items" className={cn(buttonVariants({ size: "sm" }))}>
          Inspect items
        </Link>
        <Link
          href="/admin/reports"
          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
        >
          Reports
        </Link>
        <Link
          href="/admin/users"
          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
        >
          Users
        </Link>
      </CardContent>
    </Card>
  );
}
