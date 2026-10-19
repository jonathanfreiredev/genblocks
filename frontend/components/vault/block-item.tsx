import { AssetPlate } from "@/components/vault/asset-plate";
import { CodeTabs } from "@/components/vault/code-tabs";
import { EvidencePanel } from "@/components/vault/evidence-panel";
import { ItemDetails } from "@/components/vault/item-details";
import { judgedFrom } from "@/lib/vault/judged";
import type { Component, Generation } from "@/lib/vault/types";

/**
 * One block, as a page rather than a dialog.
 *
 * The title is the only thing above the render. Below it the page splits the way
 * a reader works: the code and the brief on the left, the evidence on the right
 * in a column deliberately narrower than half.
 */
export function BlockItem({
  component,
  generations,
  categoryName,
}: {
  component: Component;
  generations: Generation[];
  categoryName: string;
}) {
  const generation =
    generations.find((one) => one.id === component.winning_generation_id) ??
    generations.at(-1) ??
    null;

  return (
    <div className="flex flex-1 flex-col px-3 py-4 md:px-4">
      <h1 className="text-2xl font-semibold tracking-tight text-balance">
        {component.title}
      </h1>

      <div className="bg-muted/20 mt-4 rounded-xl border p-2 sm:p-3">
        <div className="relative mx-auto aspect-[16/10] max-h-[58svh] w-full max-w-6xl">
          <AssetPlate
            path={
              generation?.screenshot_path ?? component.screenshot_path ?? ""
            }
            alt={`The rendered block: ${component.title}`}
            sizes="(min-width: 1280px) 1100px, 100vw"
            caption={generation?.model ?? "Model not recorded"}
            fit="contain"
            className="size-full rounded-lg"
          />
        </div>
      </div>

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0">
          <CodeTabs
            files={component.files}
            entry={component.entry}
            prompt={component.delivery_prompt}
            dependencies={component.dependencies}
          />
        </div>

        <aside className="min-w-0">
          <EvidencePanel
            kind="component"
            judged={judgedFrom(generation)}
            showVerdict={false}
            showModel={false}
            showTrace={false}
            details={
              <ItemDetails
                description={component.description}
                category={categoryName}
                date={component.created_at}
                model={generation?.model ?? null}
                traceId={generation?.langfuse_trace_id ?? null}
              />
            }
          />
        </aside>
      </div>
    </div>
  );
}
