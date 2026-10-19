import { AssetPlate } from "@/components/vault/asset-plate";
import { EvidencePanel } from "@/components/vault/evidence-panel";
import { judgedFrom } from "@/lib/vault/judged";
import type { Generation } from "@/lib/vault/types";

/**
 * What one task produced, as its own page reads it.
 *
 * A task makes one artifact, so this is a result rather than a history: the
 * render the run left and the numbers the judge gave it, one under the other.
 * It matters most when the run published nothing — a refused block has no item
 * to open, and this is the only place its evidence can be read at all.
 */
export function TaskResult({
  generation,
  brief,
}: {
  generation: Generation;
  brief: string;
}) {
  return (
    <div className="flex flex-col gap-4">
      {generation.screenshot_path ? (
        <div className="bg-muted/20 rounded-xl border p-2">
          <AssetPlate
            path={generation.screenshot_path}
            alt={`The block this task produced: ${brief}`}
            sizes="(min-width: 1024px) 900px, 100vw"
            caption={generation.model ?? "Model not recorded"}
            fit="contain"
            className="aspect-[16/10] w-full rounded-lg"
          />
        </div>
      ) : (
        <p className="text-muted-foreground text-sm">
          No render was taken for this run.
        </p>
      )}

      <EvidencePanel kind="component" judged={judgedFrom(generation)} />
    </div>
  );
}
