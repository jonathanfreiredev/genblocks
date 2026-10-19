import { AssetPlate } from "@/components/vault/asset-plate";
import { EvidencePanel } from "@/components/vault/evidence-panel";
import { judgedFrom } from "@/lib/vault/judged";
import type { Generation } from "@/lib/vault/types";

/**
 * What one task produced, as its own page reads it.
 *
 * A task makes one artifact, so this is a result rather than a history: the
 * render the run left and the numbers the judge gave it, side by side in one
 * block. It matters most when the run published nothing — a refused block has no
 * item to open, and this is the only place its evidence can be read at all.
 *
 * Its own component rather than markup inside the page for one reason: the page
 * is a server component behind a session, and the two cases worth pinning down
 * here — a run with a render, and a run that never got as far as a page — are
 * cheaper to hold than a login in the e2e suite.
 */
export function TaskResult({
  generation,
  brief,
}: {
  generation: Generation;
  brief: string;
}) {
  return (
    <div className="border-rule flex flex-col border">
      {generation.screenshot_path ? (
        <div className="p-6 pb-0">
          <AssetPlate
            path={generation.screenshot_path}
            alt={`The block this task produced: ${brief}`}
            sizes="(min-width: 1024px) 900px, 100vw"
            caption={generation.model ?? "Model not recorded"}
            className="aspect-[16/10]"
          />
        </div>
      ) : (
        <p className="type-meta text-ink-soft p-6 pb-0">
          No render was taken for this run.
        </p>
      )}

      <EvidencePanel kind="component" judged={judgedFrom(generation)} />
    </div>
  );
}
