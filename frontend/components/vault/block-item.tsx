import { ReportDialog } from "@/components/reports/report-dialog";
import { AssetPlate } from "@/components/vault/asset-plate";
import { CodeTabs } from "@/components/vault/code-tabs";
import { EvidencePanel } from "@/components/vault/evidence-panel";
import { ItemDetails } from "@/components/vault/item-details";
import { LivePreview } from "@/components/vault/live-preview";
import { highlightCodeTokens } from "@/lib/highlighter";
import { languageFor } from "@/lib/vault/code-language";
import { judgedFrom } from "@/lib/vault/judged";
import type { Component, Generation } from "@/lib/vault/types";

/**
 * One block, as a page rather than a dialog.
 *
 * The render comes first. Below it the page splits the way a reader works: the
 * code and the brief on the left, the evidence on the right in a column
 * deliberately narrower than half. The title belongs with the facts, not above
 * the picture — the prompt tab already carries the words that made it.
 */
export async function BlockItem({
  component,
  generations,
  categoryName,
  signedIn,
}: {
  component: Component;
  generations: Generation[];
  categoryName: string;
  signedIn: boolean;
}) {
  const generation =
    generations.find((one) => one.id === component.winning_generation_id) ??
    generations.at(-1) ??
    null;

  // Highlighting on the server keeps Shiki out of the item page's client
  // bundle and off its main thread. The client only renders the tokens.
  const highlighted = Object.fromEntries(
    await Promise.all(
      Object.keys(component.files)
        .sort()
        .map(async (path) => [
          path,
          await highlightCodeTokens(component.files[path], languageFor(path)),
        ]),
    ),
  );

  return (
    <div className="flex flex-1 flex-col px-3 py-4 md:px-4">
      <div className="bg-muted/20 rounded-xl border p-2 sm:p-3">
        {component.has_preview ? (
          <LivePreview componentId={component.id} title={component.title} />
        ) : (
          <div className="relative mx-auto aspect-[16/10] max-h-[58svh] w-full max-w-6xl">
            <AssetPlate
              path={
                generation?.screenshot_path ?? component.screenshot_path ?? ""
              }
              alt={`The rendered block: ${component.title}`}
              sizes="(min-width: 1280px) 1100px, 100vw"
              caption={generation?.model ?? "Model not recorded"}
              priority
              className="size-full rounded-lg"
            />
          </div>
        )}
      </div>
      <p className="text-muted-foreground mt-2 px-1 text-xs">
        {component.has_preview
          ? "Interactive preview, sandboxed: nothing you type leaves this page."
          : "This block has no interactive build yet — showing the render it was published from."}
      </p>

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0">
          <CodeTabs
            files={component.files}
            entry={component.entry}
            prompt={component.delivery_prompt}
            dependencies={component.dependencies}
            highlighted={highlighted}
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
                title={component.title}
                category={categoryName}
                date={component.created_at}
                model={generation?.model ?? null}
                traceId={generation?.langfuse_trace_id ?? null}
                provenance={component.provenance}
              />
            }
          />
          <div className="mt-2 flex justify-end">
            <ReportDialog
              targetKind="component"
              targetId={component.id}
              signedIn={signedIn}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
