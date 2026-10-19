"use client";

import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { CopyButton } from "@/components/copy-button";
import { AssetPlate } from "@/components/vault/asset-plate";
import { EvidencePanel } from "@/components/vault/evidence-panel";
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
import { judgedFrom } from "@/lib/vault/judged";
import type { Component, Generation, Image } from "@/lib/vault/types";

/**
 * The item view: the specimen on the left, the evidence on the right.
 *
 * The dialog is not local state — it is a query parameter, so a link to an item
 * exists, Back closes it, and the page around it is server-rendered either way.
 *
 * The evidence column is a third of the dialog and not half of it: a task makes
 * one artifact now, so there is no history to walk beside the numbers, and the
 * specimen is where the room should go.
 */
function Shell({
  title,
  meta,
  description,
  closeHref,
  specimen,
  evidence,
}: {
  title: string;
  meta: string;
  description?: string;
  closeHref: string;
  specimen: ReactNode;
  evidence: ReactNode;
}) {
  const router = useRouter();

  return (
    <Dialog
      open
      onOpenChange={(next) => {
        if (!next) {
          router.push(closeHref);
        }
      }}
    >
      <DialogContent className="gap-0 overflow-hidden p-0 sm:max-w-5xl">
        <DialogHeader className="border-rule gap-2 border-b px-6 py-5">
          <DialogTitle className="type-title">{title}</DialogTitle>
          <p className="type-meta text-ink-faint">{meta}</p>
          {description ? (
            <DialogDescription className="max-w-[72ch]">
              {description}
            </DialogDescription>
          ) : null}
        </DialogHeader>

        <div className="grid max-h-[72svh] overflow-y-auto lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div className="border-rule bg-paper flex min-w-0 flex-col border-b lg:border-r lg:border-b-0">
            {specimen}
          </div>
          {evidence}
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
 */
function FileRail({
  paths,
  chosen,
  onChoose,
}: {
  paths: string[];
  chosen: string;
  onChoose: (path: string) => void;
}) {
  return (
    <div className="border-rule shrink-0 border-b lg:w-52 lg:border-r lg:border-b-0">
      <div className="bg-panel-sunken flex flex-wrap gap-x-4 gap-y-1 px-4 py-3 lg:sticky lg:top-0 lg:flex-col lg:flex-nowrap lg:gap-y-1.5">
        <span className="type-label text-ink-faint lg:mb-1">Files</span>
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
    <div className="border-rule bg-panel-sunken flex items-center justify-between gap-4 border-t px-5 py-3">
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
 * A task produces one artifact, so there is no history to walk: the code pane
 * reads the project that run left, file by file, and the panel beside it carries
 * the numbers that run earned.
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
  const [tab, setTab] = useState("code");
  const [file, setFile] = useState<string | null>(null);

  // One artifact per task: the one the block was published from, and the newest
  // if a run ever makes more than one.
  const generation =
    generations.find((one) => one.id === component.winning_generation_id) ??
    generations.at(-1) ??
    null;

  // A block is a project, so the pane reads one file of it at a time and says
  // which; a seeded block, which has no files, is still one file and still reads.
  const files = generation?.files ?? component.files;
  const paths = files ? Object.keys(files).sort() : [];
  const shown = file !== null && paths.includes(file) ? file : paths[0];
  const code =
    shown !== undefined
      ? (files?.[shown] ?? "")
      : (generation?.code ?? component.code);

  return (
    <Shell
      title={component.title}
      meta={`${typeName} · ${component.slug} · ${formatDate(component.created_at)}`}
      description={component.description}
      closeHref={closeHref}
      specimen={
        <Tabs
          value={tab}
          onValueChange={(value) => setTab(String(value))}
          className="min-w-0 gap-0"
        >
          <div className="border-rule flex items-center justify-between gap-4 border-b pr-4">
            <TabsList variant="line" className="pl-4">
              <TabsTrigger value="code">Code</TabsTrigger>
              <TabsTrigger value="render">Render</TabsTrigger>
              <TabsTrigger value="prompt">Delivery prompt</TabsTrigger>
            </TabsList>

            {tab === "prompt" ? (
              <CopyButton
                text={component.delivery_prompt}
                idleLabel="Copy the delivery prompt"
              />
            ) : null}
            {tab === "code" ? (
              <CopyButton
                text={code}
                idleLabel={
                  shown !== undefined ? `Copy ${shown}` : "Copy the code"
                }
              />
            ) : null}
          </div>

          <TabsContent value="code" className="p-0">
            <div className="flex flex-col lg:flex-row">
              {shown !== undefined ? (
                <FileRail paths={paths} chosen={shown} onChoose={setFile} />
              ) : null}
              <pre className="type-code bg-ink text-on-ink min-w-0 flex-1 overflow-x-auto p-5">
                {code}
              </pre>
            </div>
            <InstallLine dependencies={component.dependencies} />
          </TabsContent>

          <TabsContent value="render" className="p-0">
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

          <TabsContent value="prompt" className="p-0">
            <p className="type-body text-ink-soft max-w-[72ch] p-6">
              {component.delivery_prompt}
            </p>
          </TabsContent>
        </Tabs>
      }
      evidence={
        <EvidencePanel kind="component" judged={judgedFrom(generation)} />
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
      specimen={
        <div className="flex flex-col gap-5 p-5">
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
      evidence={
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
        />
      }
    />
  );
}
