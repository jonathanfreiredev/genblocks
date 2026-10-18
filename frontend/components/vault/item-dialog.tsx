"use client";

import { useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { CopyButton } from "@/components/copy-button";
import { AssetPlate } from "@/components/vault/asset-plate";
import { EvidencePanel, type Judged } from "@/components/vault/evidence-panel";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { dimensions, formatDate, formatTime } from "@/lib/vault/format";
import type { Component, Generation, Image } from "@/lib/vault/types";
import { cn } from "@/lib/utils";

/**
 * The item view: the specimen on the left, the evidence on the right.
 *
 * The dialog is not local state — it is a query parameter, so a link to an item
 * exists, Back closes it, and the page around it is server-rendered either way.
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

        <div className="grid max-h-[72svh] overflow-y-auto lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
          <div className="border-rule bg-paper flex min-w-0 flex-col border-b lg:border-r lg:border-b-0">
            {specimen}
          </div>
          {evidence}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function AttemptCaption({
  attemptNo,
  total,
  createdAt,
}: {
  attemptNo: number | null;
  total: number;
  createdAt: string;
}) {
  return (
    <div className="type-label text-ink-faint flex items-baseline justify-between gap-4 px-5 py-3">
      <span>
        {attemptNo === null
          ? "Published"
          : `Attempt № ${attemptNo} of ${total}`}
      </span>
      <span className="tabular-nums">
        {formatDate(createdAt)} {formatTime(createdAt)}
      </span>
    </div>
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

/** The files of a project, as a strip a reader can walk file by file. */
function FileStrip({
  paths,
  chosen,
  onChoose,
}: {
  paths: string[];
  chosen: string;
  onChoose: (path: string) => void;
}) {
  return (
    <div className="border-rule bg-panel-sunken flex flex-wrap items-baseline gap-x-4 gap-y-1 border-b px-5 py-2">
      <span className="type-label text-ink-faint">Files</span>
      {paths.map((path) => (
        <button
          key={path}
          type="button"
          onClick={() => onChoose(path)}
          aria-pressed={path === chosen}
          className={cn(
            "type-code cursor-pointer",
            path === chosen ? "text-ink" : "text-ink-faint hover:text-ink",
          )}
        >
          {path}
        </button>
      ))}
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
 * A block, with its whole attempt history.
 *
 * The code on screen belongs to the attempt selected in the ledger, so the
 * rejected first pass is readable beside the number that rejected it. That
 * contrast is the product's argument; hiding it behind a filter would be a
 * decision against the thing being sold.
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
  const [selectedId, setSelectedId] = useState<string | null>(
    component.winning_generation_id ?? generations.at(-1)?.id ?? null,
  );
  const [tab, setTab] = useState("code");
  const [file, setFile] = useState<string | null>(null);

  const selected =
    generations.find((generation) => generation.id === selectedId) ?? null;

  // The project the attempt produced, when there is one. A block is a project
  // now, so the pane reads one file of it at a time and says which; an attempt
  // (or a seeded block) with no files is still one file, and still readable.
  const files = selected?.files ?? component.files;
  const paths = files ? Object.keys(files).sort() : [];
  const shown = file !== null && paths.includes(file) ? file : paths[0];
  const code =
    shown !== undefined
      ? (files?.[shown] ?? "")
      : (selected?.code ?? component.code);

  const judged: Judged = {
    scores: selected?.scores ?? null,
    verdict: selected?.verdict ?? "candidate",
    rubricVersion: selected?.rubric_version ?? null,
    model: selected?.model ?? null,
    traceId: selected?.langfuse_trace_id ?? null,
    checks: selected?.checks ?? null,
  };

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

            <CopyButton
              text={tab === "prompt" ? component.delivery_prompt : code}
              idleLabel={
                tab === "prompt" ? "Copy the delivery prompt" : "Copy the code"
              }
            />
          </div>

          <TabsContent value="code" className="p-0">
            <AttemptCaption
              attemptNo={selected?.attempt_no ?? null}
              total={generations.length}
              createdAt={selected?.created_at ?? component.created_at}
            />
            {shown !== undefined ? (
              <FileStrip paths={paths} chosen={shown} onChoose={setFile} />
            ) : null}
            <pre className="type-code bg-ink text-on-ink overflow-x-auto p-5">
              {code}
            </pre>
            <InstallLine dependencies={component.dependencies} />
          </TabsContent>

          <TabsContent value="render" className="p-0">
            <AttemptCaption
              attemptNo={selected?.attempt_no ?? null}
              total={generations.length}
              createdAt={selected?.created_at ?? component.created_at}
            />
            {/* The render of the attempt selected in the ledger, which is the
                same history the code pane shows. A run that never got as far as
                a page says so rather than showing an empty frame. */}
            <AssetPlate
              path={selected?.screenshot_path ?? ""}
              alt={`The rendered block: ${component.title}`}
              sizes="(min-width: 1024px) 620px, 100vw"
              caption={
                selected?.screenshot_path
                  ? (selected.model ?? "Model not recorded")
                  : "No render was taken for this attempt."
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
        <EvidencePanel
          kind="component"
          judged={judged}
          attempts={generations}
          selectedAttempt={selected?.attempt_no}
          onSelectAttempt={(attempt) =>
            setSelectedId(
              generations.find(
                (generation) => generation.attempt_no === attempt,
              )?.id ?? null,
            )
          }
        />
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
 * An image carries its scores directly instead of an attempt history, because a
 * standalone image is its own judged artifact. Its verdict is not stored either:
 * the library only holds pieces that passed, so a scored row is a published one.
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
            sizes="(min-width: 1024px) 620px, 100vw"
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
            // An image is scored as it enters the library: nothing sandboxes it.
            checks: null,
          }}
        />
      }
    />
  );
}
