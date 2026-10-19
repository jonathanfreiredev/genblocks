import { AppShell } from "@/components/shell/app-shell";
import { listCategories } from "@/lib/vault/api";
import type { Category } from "@/lib/vault/types";
import { getSession } from "@/server/auth/auth.lib";

export default async function Layout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const session = await getSession();

  // The sidebar is chrome: a vault that cannot be read must not take the page
  // down with it. The gallery itself catches the same failure and says so.
  let categories: Category[] = [];
  try {
    categories = await listCategories();
  } catch {
    categories = [];
  }

  return (
    <AppShell session={session} categories={categories}>
      {children}
    </AppShell>
  );
}
