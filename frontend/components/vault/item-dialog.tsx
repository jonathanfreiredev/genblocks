"use client";

import {
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { CopyButton } from "@/components/copy-button";
import { AssetPlate } from "@/components/vault/asset-plate";
import { EvidencePanel } from "@/components/vault/evidence-panel";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { dimensions, formatDate } from "@/lib/vault/format";
import type { Judged } from "@/lib/vault/judged";
import { judgedFrom } from "@/lib/vault/judged";
import type { Component, Generation, Image, Kind } from "@/lib/vault/types";

/**
 * The handle a side panel collapses to, and the way back.
 *
 * A panel that can be hidden says so where it lives rather than in a menu: the
 * reader decides what to keep in view, and the button stays where the panel was
 * so the decision is reversible from the same spot.
 */
function PanelToggle({
  side,
  open,
  what,
  onClick,
}: {
  side: "left" | "right";
  open: boolean;
  what: string;
  onClick: () => void;
}) {
  const label = open ? `Hide the ${what}` : `Show the ${what}`;
  const Icon =
    side === "left"
      ? open
        ? PanelLeftClose
        : PanelLeftOpen
      : open
        ? PanelRightClose
        : PanelRightOpen;

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      onClick={onClick}
      aria-label={label}
      aria-expanded={open}
      title={label}
    >
      <Icon className="size-4" />
    </Button>
  );
}

/**
 * The item view: the specimen on the left, the evidence on the right.
 *
 * The dialog is not local state — it is a query parameter, so a link to an item
 * exists, Back closes it, and the page around it is server-rendered either way.
 *
 * The specimen is where the room goes, so the evidence column is a third of the
 * dialog rather than half of it, and it collapses: a reader who came for the code
 * can give it the whole width, and a reader who came for the numbers can keep
 * them while the specimen stays out of the way. Both columns scroll on their own,
 * so the toolbar and the numbers stay put however long the file is.
 */
function Shell({
  title,
  meta,
  description,
  closeHref,
  kind,
  judged,
  specimen,
}: {
  title: string;
  meta: string;
  description?: string;
  closeHref: string;
  kind: Kind;
  judged: Judged;
  specimen: ReactNode;
}) {
  const router = useRouter();
  const [scoresOpen, setScoresOpen] = useState(true);

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) {
          router.push(closeHref);
        }
      }}
    >
      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-5xl lg:flex lg:max-h-[88svh] lg:flex-col">
        <DialogHeader className="border-rule shrink-0 gap-2 border-b px-6 py-5">
          <DialogTitle className="type-title">{title}</DialogTitle>
          <p className="type-meta text-ink-faint">{meta}</p>
          {description ? (
            <DialogDescription className="max-w-[72ch]">
              {description}
            </DialogDescription>
          ) : null}
        </DialogHeader>

        <div
          className={cn(
            "grid max-h-[72svh] overflow-y-auto lg:max-h-none lg:min-h-0 lg:flex-1 lg:overflow-hidden",
            scoresOpen
              ? "lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]"
              : "lg:grid-cols-[minmax(0,1fr)_auto]",
          )}
        >
          <div className="border-rule bg-paper flex min-h-0 min-w-0 flex-col border-b lg:h-full lg:overflow-hidden lg:border-r lg:border-b-0">
            {specimen}
          </div>

          {scoresOpen ? (
            <aside className="min-h-0 min-w-0 lg:h-full lg:overflow-y-auto">
              <EvidencePanel
                kind={kind}
                judged={judged}
                showVerdict={false}
                action={
                  <PanelToggle
                    side="right"
                    open
                    what="scores"
                    onClick={() => setScoresOpen(false)}
                  />
                }
              />
            </aside>
          ) : (
            <div className="flex justify-center py-1 lg:h-full lg:w-11 lg:flex-col lg:items-center lg:justify-start lg:py-2">
              <PanelToggle
                side="right"
                open={false}
                what="scores"
                onClick={() => setScoresOpen(true)}
              />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

/**
 * What a block needs installed beside it.
 *
 * React is what a block is written in rather than something it asks anybody to
 * add: listing it would put a two-package install line under every block in the
 * registry, and the part worth reading is what it adds on top of it.
 */
const IMPLIED_INSTALLS = new Set(["react", "react-dom"]);

/**
 * The files of a project, as a rail a reader can walk file by file.
 *
 * The rail is as tall as the code beside it — the pane is a two-column split, not
 * a list floating over it — but only the list itself is tinted: a file or two
 * against a full-height block of grey reads as an empty column, which is what it
 * is. The names stay put while the code scrolls, because a long file is exactly
 * when somebody wants to jump to another one.
 *
 * It collapses to its own handle: with the files out of the way a wide file gets
 * the width, which is the other half of the same reason.
 */
function FileRail({
  paths,
  chosen,
  onChoose,
  open,
  onToggle,
}: {
  paths: string[];
  chosen: string;
  onChoose: (path: string) => void;
  open: boolean;
  onToggle: () => void;
}) {
  if (!open) {
    return (
      <div className="border-rule flex shrink-0 justify-center border-b px-1 py-1 lg:h-full lg:flex-col lg:items-center lg:justify-start lg:border-r lg:border-b-0 lg:py-2">
        <PanelToggle side="left" open={false} what="files" onClick={onToggle} />
      </div>
    );
  }

  return (
    <div className="border-rule shrink-0 border-b lg:h-full lg:w-52 lg:overflow-y-auto lg:border-r lg:border-b-0">
      <div className="bg-panel-sunken flex flex-wrap items-center gap-x-4 gap-y-1 px-3 py-2 lg:flex-col lg:flex-nowrap lg:items-stretch lg:gap-y-1.5">
        <div className="flex items-center justify-between gap-2 lg:mb-1">
          <span className="type-label text-ink-faint">Files</span>
          <PanelToggle side="left" open what="files" onClick={onToggle} />
        </div>

        {paths.map((path) => (
          <button
            key={path}
            type="button"
            onClick={() => onChoose(path)}
            aria-pressed={path === chosen}
            title={path}
            className={cn(
              "type-code max-w-full cursor-pointer truncate text-left",
              path === chosen ? "text-ink" : "text-ink-faint hover:text-ink",
            )}
          >
            {path}
          </button>
        ))}
      </div>
    </div>
  );
}

/** The install line, as the command that does it. */
function InstallLine({
  dependencies,
}: {
  dependencies: Record<string, string> | null;
}) {
  const added = Object.entries(dependencies ?? {}).filter(
    ([name]) => !IMPLIED_INSTALLS.has(name),
  );
  if (added.length === 0) {
    return null;
  }

  const command = `pnpm add ${added
    .map(([name, range]) => `${name}@${range}`)
    .join(" ")}`;

  return (
    <div className="border-rule bg-panel-sunken flex shrink-0 items-center justify-between gap-4 border-t px-5 py-3">
      <p className="type-meta text-ink-soft truncate">
        <span className="text-ink-faint">Install </span>
        {command}
      </p>
      <CopyButton text={command} idleLabel="Copy the install command" />
    </div>
  );
}

/**
 * A block, and the run that made it.
 *
 * It opens on the render, because that is what somebody browsing came to see, and
 * the numbers are already beside it. The code is a tab away, and there the two
 * columns a reader might want — the files and the scores — are both open until
 * they say otherwise.
 */
export function ComponentDialog({
  component,
  generations,
  typeName,
  closeHref,
}: {
  component: Component;
  generations: Generation[];
  typeName: string;
  closeHref: string;
}) {
  const [tab, setTab] = useState("render");
  const [file, setFile] = useState<string | null>(null);
  const [filesOpen, setFilesOpen] = useState(true);

  // One artifact per task: the one the block was published from, and the newest
  // if a run ever makes more than one.
  const generation =
    generations.find((one) => one.id === component.winning_generation_id) ??
    generations.at(-1) ??
    null;

  // A block is a project, so the pane reads one file of it at a time. The file
  // that opens is the entry the block names, never the alphabetically first one:
  // `src/App.tsx` sorts before `src/Block.tsx` and is not what the page imports.
  const files = generation?.files ?? component.files;
  const entry = generation?.entry ?? component.entry;
  const paths = Object.keys(files).sort();
  const shown = file !== null && paths.includes(file) ? file : entry;
  const code = files[shown] ?? "";

  return (
    <Shell
      title={component.title}
      meta={`${typeName} · ${component.slug} · ${formatDate(component.created_at)}`}
      description={component.description}
      closeHref={closeHref}
      kind="component"
      judged={judgedFrom(generation)}
      specimen={
        <Tabs
          value={tab}
          onValueChange={(value) => setTab(String(value))}
          className="min-w-0 gap-0 lg:h-full lg:min-h-0 lg:flex-col"
        >
          <div className="border-rule bg-paper flex shrink-0 items-center justify-between gap-4 border-b pr-4">
            <TabsList variant="line" className="pl-4">
              <TabsTrigger value="render">Render</TabsTrigger>
              <TabsTrigger value="code">Code</TabsTrigger>
              <TabsTrigger value="prompt">Delivery prompt</TabsTrigger>
            </TabsList>

            {tab === "prompt" ? (
              <CopyButton
                text={component.delivery_prompt}
                idleLabel="Copy the delivery prompt"
              />
            ) : null}
            {tab === "code" ? (
              <CopyButton text={code} idleLabel={`Copy ${shown}`} />
            ) : null}
          </div>

          <TabsContent
            value="render"
            className="min-h-0 p-0 lg:flex-1 lg:overflow-y-auto"
          >
            {/* The render that run produced. A run that never got as far as a page
                says so rather than showing an empty frame. */}
            <AssetPlate
              path={generation?.screenshot_path ?? ""}
              alt={`The rendered block: ${component.title}`}
              sizes="(min-width: 1024px) 680px, 100vw"
              caption={
                generation?.screenshot_path
                  ? (generation.model ?? "Model not recorded")
                  : "No render was taken for this run."
              }
              className="aspect-[16/10]"
            />
          </TabsContent>

          <TabsContent
            value="code"
            className="min-h-0 p-0 lg:flex lg:flex-1 lg:flex-col lg:overflow-hidden"
          >
            <div className="flex min-h-0 flex-col lg:flex-1 lg:flex-row lg:overflow-hidden">
              <FileRail
                paths={paths}
                chosen={shown}
                onChoose={setFile}
                open={filesOpen}
                onToggle={() => setFilesOpen((open) => !open)}
              />
              <pre className="type-code bg-ink text-on-ink min-h-0 min-w-0 flex-1 overflow-auto p-5 lg:h-full">
                {code}
              </pre>
            </div>
            <InstallLine dependencies={component.dependencies} />
          </TabsContent>

          <TabsContent
            value="prompt"
            className="min-h-0 p-0 lg:flex-1 lg:overflow-y-auto"
          >
            <p className="type-body text-ink-soft max-w-[72ch] p-6">
              {component.delivery_prompt}
            </p>
          </TabsContent>
        </Tabs>
      }
    />
  );
}

function RecipeRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-rule flex items-baseline justify-between gap-6 border-t py-2.5">
      <dt className="type-label text-ink-faint">{label}</dt>
      <dd className="type-meta text-ink-soft truncate">{value}</dd>
    </div>
  );
}

/**
 * A stock image.
 *
 * An image carries its scores directly instead of a producing task, because it is
 * its own judged artifact. Its verdict is not stored either: the library only
 * holds pieces that passed, so a scored row is a published one.
 *
 * There are no tabs here: the picture is the specimen and the prompt is its
 * caption, so the whole view is one reading. The scores still collapse, which is
 * how a reader gets the picture at the full width of the dialog.
 */
export function ImageDialog({
  image,
  typeName,
  closeHref,
}: {
  image: Image;
  typeName: string;
  closeHref: string;
}) {
  return (
    <Shell
      title={typeName}
      meta={`${dimensions(image.width, image.height)} · ${image.model ?? "unknown model"} · ${formatDate(image.created_at)}`}
      closeHref={closeHref}
      kind="image"
      judged={{
        scores: image.scores,
        verdict: image.scores ? "published" : "candidate",
        rubricVersion: image.rubric_version,
        model: image.model,
        traceId: image.langfuse_trace_id,
        checks: null,
      }}
      specimen={
        <div className="flex min-h-0 flex-col gap-5 p-5 lg:h-full lg:overflow-y-auto">
          <div className="flex items-start justify-between gap-4">
            <p className="type-body text-ink max-w-[72ch]">{image.prompt}</p>
            <CopyButton text={image.prompt} idleLabel="Copy the prompt" />
          </div>

          <AssetPlate
            path={image.path}
            alt={image.prompt}
            sizes="(min-width: 1024px) 680px, 100vw"
            caption={dimensions(image.width, image.height)}
            className="border-rule aspect-[3/2] border"
          />

          <dl className="flex flex-col">
            <RecipeRow label="Model" value={image.model ?? "Unknown"} />
            <RecipeRow
              label="Dimensions"
              value={dimensions(image.width, image.height)}
            />
            <RecipeRow label="Licence" value={image.license} />
            <RecipeRow label="Asset" value={image.path} />
          </dl>
        </div>
      }
    />
  );
}
