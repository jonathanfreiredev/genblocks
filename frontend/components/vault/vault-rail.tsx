import { GenerateDialog } from "@/components/vault/generate-dialog";
import { KindNav, TaxonomyNav } from "@/components/vault/taxonomy-nav";
import type { CatalogueView } from "@/lib/vault/links";
import type { Category } from "@/lib/vault/types";

/**
 * The lateral navigation: the one action the vault has, then the taxonomy that
 * organises it. It stacks above the sheet on a phone, where the same links
 * become a row.
 *
 * `min-w-0` is load-bearing: the type list is a row of links that never wrap, so
 * without it this column's min-content — a couple of thousand pixels of
 * taxonomy — would size the grid track and push the whole sheet off the screen.
 */
export function VaultRail({
  view,
  types,
}: {
  view: CatalogueView;
  types: Category[];
}) {
  return (
    <div className="flex min-w-0 flex-col gap-6 lg:self-start">
      <GenerateDialog />

      <KindNav view={view} />

      <div className="border-rule border-t pt-4">
        <TaxonomyNav view={view} types={types} />
      </div>
    </div>
  );
}
