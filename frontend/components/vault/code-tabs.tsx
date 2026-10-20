"use client";

import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useState } from "react";

import { CopyButton } from "@/components/copy-button";
import { Button } from "@/components/ui/button";
import {
  CodeBlock,
  CodeBlockActions,
  CodeBlockContent,
  CodeBlockCopyButton,
  CodeBlockLine,
} from "@/components/ui/code-block";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useHighlightedCode } from "@/hooks/use-highlighted-code";
import { cn } from "@/lib/utils";

/**
 * What a block needs installed beside it. React is the language, not a request.
 */
const IMPLIED_INSTALLS = new Set(["react", "react-dom"]);

/** Shiki grammar per file extension; anything else is shown as plain text. */
const LANGUAGE_BY_EXTENSION: Record<string, string> = {
  css: "css",
  html: "html",
  js: "javascript",
  jsx: "jsx",
  json: "json",
  md: "markdown",
  mdx: "markdown",
  py: "python",
  sh: "bash",
  sql: "sql",
  ts: "typescript",
  tsx: "tsx",
  yaml: "yaml",
  yml: "yaml",
};

function languageFor(path: string): string {
  const extension = path.slice(path.lastIndexOf(".") + 1).toLowerCase();

  return LANGUAGE_BY_EXTENSION[extension] ?? "text";
}

/**
 * The project's files.
 *
 * Left of the code on a laptop, a strip above it on a phone; both are the same
 * list and both collapse with the same button, because a reader who wants one
 * file wide should not have to lose the list to get it.
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
  return (
    <div
      className={cn(
        "bg-muted/30 flex shrink-0 flex-col border-b lg:h-full lg:border-r lg:border-b-0",
        open ? "lg:w-44" : "lg:w-10",
      )}
    >
      <div className="flex items-center justify-between gap-1 px-2 py-1 lg:border-b">
        {open ? (
          <span className="text-muted-foreground text-xs font-medium">
            Files
          </span>
        ) : null}
        <Button
          type="button"
          variant="ghost"
          size="icon-xs"
          onClick={onToggle}
          aria-label={open ? "Hide the files" : "Show the files"}
          aria-expanded={open}
          className={cn("ml-auto", !open && "lg:mx-auto")}
        >
          {open ? <PanelLeftClose /> : <PanelLeftOpen />}
        </Button>
      </div>

      {open ? (
        <div className="flex gap-1 overflow-x-auto p-1 lg:flex-1 lg:flex-col lg:gap-0.5 lg:overflow-x-visible lg:overflow-y-auto">
          {paths.map((path) => (
            <button
              key={path}
              type="button"
              onClick={() => onChoose(path)}
              aria-pressed={path === chosen}
              title={path}
              className={cn(
                "shrink-0 rounded-md px-2 py-1 text-left font-mono text-xs whitespace-nowrap transition-colors lg:w-full lg:truncate",
                path === chosen
                  ? "bg-background text-foreground shadow-xs"
                  : "text-muted-foreground hover:bg-background/60 hover:text-foreground",
              )}
            >
              {path}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

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
    <div className="bg-muted/30 flex items-center justify-between gap-4 border-t px-4 py-2">
      <p className="text-muted-foreground truncate font-mono text-xs">
        <span className="text-foreground/60">$ </span>
        {command}
      </p>
      <CopyButton text={command} idleLabel="Copy the install command" />
    </div>
  );
}

/**
 * The left half of an item: the project's files under one tab, the brief under
 * another. The render lives above both, so there is no third tab for it.
 */
export function CodeTabs({
  files,
  entry,
  prompt,
  dependencies,
}: {
  files: Record<string, string>;
  entry: string;
  prompt: string;
  dependencies: Record<string, string> | null;
}) {
  const paths = Object.keys(files).sort();
  const [tab, setTab] = useState("code");
  const [chosen, setChosen] = useState(entry);
  const [railOpen, setRailOpen] = useState(true);

  const shown = paths.includes(chosen) ? chosen : entry;
  const code = files[shown] ?? "";
  const lines = useHighlightedCode(code, languageFor(shown));

  return (
    <Tabs
      value={tab}
      onValueChange={(value) => setTab(String(value))}
      className="bg-card gap-0 rounded-xl border"
    >
      <div className="flex items-center justify-between gap-2 border-b pr-2">
        <TabsList variant="line" className="px-2">
          <TabsTrigger value="code">code</TabsTrigger>
          <TabsTrigger value="prompt">prompt</TabsTrigger>
        </TabsList>
        {tab === "prompt" ? (
          <CopyButton text={prompt} idleLabel="Copy the prompt" />
        ) : null}
      </div>

      <TabsContent value="code" className="flex flex-col">
        <div className="flex h-[clamp(17rem,52svh,38rem)] min-h-0 flex-col lg:flex-row">
          <FileRail
            paths={paths}
            chosen={shown}
            onChoose={setChosen}
            open={railOpen}
            onToggle={() => setRailOpen((open) => !open)}
          />

          <CodeBlock
            size="sm"
            className="bg-muted/20 min-h-0 flex-1 rounded-none border-0"
          >
            <CodeBlockActions>
              <CodeBlockCopyButton value={code} />
            </CodeBlockActions>
            <CodeBlockContent lineNumbers className="min-h-0 flex-1">
              {lines.map((line, index) => (
                <CodeBlockLine key={index}>{line}</CodeBlockLine>
              ))}
            </CodeBlockContent>
          </CodeBlock>
        </div>
        <InstallLine dependencies={dependencies} />
      </TabsContent>

      <TabsContent value="prompt" className="min-h-[clamp(10rem,24svh,18rem)]">
        <p className="text-muted-foreground p-4 text-sm leading-relaxed whitespace-pre-wrap">
          {prompt}
        </p>
      </TabsContent>
    </Tabs>
  );
}
