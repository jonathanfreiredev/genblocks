import { CopyButton } from "@/components/copy-button";
import { AssetPlate } from "@/components/vault/asset-plate";
import { EvidencePanel } from "@/components/vault/evidence-panel";
import { ItemDetails } from "@/components/vault/item-details";
import type { Image } from "@/lib/vault/types";

/**
 * One stock image, with the same shape as a block: picture first, the text on
 * the left, the evidence on the right.
 *
 * An image has no code and no separate delivery prompt, so the left side is the
 * prompt it was made from. The panel still reads the same, because the claim is
 * the same: this artifact was scored, and here is how.
 */
export function ImageItem({
  image,
  categoryName,
}: {
  image: Image;
  categoryName: string;
}) {
  const ratio = `${image.width} / ${image.height}`;

  return (
    <div className="flex flex-1 flex-col px-3 py-4 md:px-4">
      <h1 className="text-2xl font-semibold tracking-tight text-balance">
        {categoryName}
      </h1>

      <div className="bg-muted/20 mt-4 rounded-xl border p-2 sm:p-3">
        <div
          className="relative mx-auto max-h-[60svh] w-full max-w-5xl"
          style={{ aspectRatio: ratio }}
        >
          <AssetPlate
            path={image.path}
            alt={image.prompt}
            sizes="(min-width: 1280px) 1000px, 100vw"
            caption={`${image.width} × ${image.height}`}
            fit="contain"
            className="size-full rounded-lg"
          />
        </div>
      </div>

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="bg-card min-w-0 rounded-xl border">
          <div className="flex items-center justify-between gap-3 border-b px-4 py-2">
            <span className="text-muted-foreground text-xs font-medium tracking-wide">
              prompt
            </span>
            <CopyButton text={image.prompt} idleLabel="Copy the prompt" />
          </div>
          <p className="p-4 text-sm leading-relaxed">{image.prompt}</p>
        </div>

        <aside className="min-w-0">
          <EvidencePanel
            kind="image"
            judged={{
              scores: image.scores,
              verdict: image.scores ? "published" : "candidate",
              rubricVersion: image.rubric_version,
              model: image.model,
              traceId: image.langfuse_trace_id,
              checks: null,
            }}
            showVerdict={false}
            showModel={false}
            showTrace={false}
            details={
              <ItemDetails
                category={categoryName}
                date={image.created_at}
                model={image.model}
                traceId={image.langfuse_trace_id}
              />
            }
          />
        </aside>
      </div>
    </div>
  );
}
