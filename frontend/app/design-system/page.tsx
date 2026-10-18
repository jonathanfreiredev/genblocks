"use client";

import * as React from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { CategoryChip } from "@/components/ui/category-chip";
import { ConsolePanel } from "@/components/ui/console-panel";
import { DarkBand } from "@/components/ui/dark-band";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import { Highlight } from "@/components/ui/highlight";
import { Input } from "@/components/ui/input";
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item";
import { Label } from "@/components/ui/label";
import { ScoreReadout } from "@/components/ui/score-readout";
import { Separator } from "@/components/ui/separator";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { toast } from "@/components/ui/toast";
import { VerdictStamp } from "@/components/ui/verdict-stamp";
import { ColorPair } from "@/components/design-system/color-pair";
import {
  StateMatrix,
  previewState,
} from "@/components/design-system/state-matrix";
import { useTheme } from "@/components/theme-toggle";

/* ------------------------------------------------------------------ layout */

const ANCHORS = [
  ["foundations", "Foundations"],
  ["actions", "Actions"],
  ["inputs", "Inputs"],
  ["navigation", "Navigation"],
  ["data", "Data display"],
  ["feedback", "Feedback"],
  ["overlays", "Overlays"],
  ["bands", "Bands"],
  ["rules", "Do and Don’t"],
  ["recipe", "Recipe"],
] as const;

function Section({
  id,
  eyebrow,
  title,
  lead,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  lead?: string;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24">
      <header className="border-hairline border-b pb-6">
        <p className="type-label text-ink-muted">{eyebrow}</p>
        <h2 className="type-title text-ink-strong mt-3">{title}</h2>
        {lead ? (
          <p className="type-body text-ink-muted mt-2 max-w-2xl">{lead}</p>
        ) : null}
      </header>
      <div className="mt-10">{children}</div>
    </section>
  );
}

function Block({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <p className="type-label text-ink-muted mb-5">{label}</p>
      {children}
    </div>
  );
}

/* -------------------------------------------------------------- foundations */

function Swatch({ token, name }: { token: string; name: string }) {
  return (
    <div className="flex flex-col gap-3">
      <div
        className="border-hairline h-16 rounded-md border"
        style={{ backgroundColor: `var(--${token})` }}
      />
      <div className="flex flex-col gap-0.5">
        <span className="type-body-sm text-ink-strong">{name}</span>
        <span className="type-mono text-ink-muted">--{token}</span>
      </div>
    </div>
  );
}

const COLOR_PAIRS: Array<[string, string, string]> = [
  ["Page", "canvas", "ink"],
  ["Card", "card", "card-foreground"],
  ["Primary pill", "primary", "primary-foreground"],
  ["Secondary", "secondary", "secondary-foreground"],
  ["Muted", "muted", "muted-foreground"],
  ["Coral chip", "coral", "on-coral"],
  ["Link on canvas", "canvas", "link"],
  ["Error", "canvas", "destructive"],
  ["Dark band", "band", "band-foreground"],
  ["Navy band", "band-alt", "band-foreground"],
  ["Pass", "verdict-pass-soft", "verdict-pass"],
  ["Retry", "verdict-retry-soft", "verdict-retry"],
  ["Fail", "verdict-fail-soft", "verdict-fail"],
];

const TYPE_ROWS: Array<[string, string, string, string]> = [
  [
    "type-display",
    "clamp(40 → 72px) · 400 · 1.0 · −0.03em",
    "The one declaration",
    "Every component, judged.",
  ],
  [
    "type-display-sm",
    "clamp(28 → 40px) · 400 · 1.05 · −0.02em",
    "Section statements",
    "The evidence panel",
  ],
  [
    "type-title",
    "24px · 500 · 1.25",
    "Card and section heads",
    "Pricing table",
  ],
  [
    "type-subtitle",
    "18px · 400 · 1.4",
    "Lead paragraphs",
    "Generated from a brief.",
  ],
  [
    "type-body",
    "16px · 400 · 1.5",
    "Default copy",
    "Every component keeps its scores.",
  ],
  ["type-body-sm", "14px · 400 · 1.4", "Controls, chips", "Generate component"],
  [
    "type-micro",
    "12px · 400 · 1.4",
    "Footer, captions",
    "Released under the MIT License",
  ],
  [
    "type-label",
    "14px mono · uppercase · 0.02em",
    "Eyebrows, categories",
    "Verdict",
  ],
  ["type-mono", "14px mono", "Metadata, tables", "№ 00217 · 2026-10-16"],
  ["type-code", "13px mono · 1.6", "Code, console", "const score = 88"],
  ["type-score", "28px mono · tabular", "Judge score", "88"],
];

const SPACING: Array<[string, number, string]> = [
  ["xs", 4, "w-1"],
  ["sm", 8, "w-2"],
  ["md", 16, "w-4"],
  ["lg", 24, "w-6"],
  ["xl", 32, "w-8"],
  ["2xl", 48, "w-12"],
  ["3xl", 64, "w-16"],
  ["4xl", 96, "w-24"],
];

const RADIUS: Array<[string, string, string]> = [
  ["rounded-sm", "4px", "utility, thumbnails"],
  ["rounded-lg", "8px", "inputs, items, small cards"],
  ["rounded-xl", "16px", "cards, dialogs"],
  ["rounded-2xl", "22px", "media cards, toasts"],
  ["rounded-4xl", "30px", "filters"],
  ["rounded-full", "pill", "buttons, category chips"],
];

/* -------------------------------------------------------------------- data */

/** What one run scored, as the evidence panel reads it out. */
const SCORES: Array<[string, number]> = [
  ["Render", 92],
  ["Accessibility", 88],
  ["Visual", 86],
  ["Copy", 90],
  ["Compliance", 94],
];

/* -------------------------------------------------------------------- page */

export default function DesignSystemPage() {
  const { isDark, toggle } = useTheme();

  return (
    <div className="mx-auto flex w-full max-w-[1200px] flex-col gap-28 px-6 py-16">
      {/* Header */}
      <header className="flex flex-col gap-10">
        <div className="flex items-center justify-between gap-4">
          <p className="type-label text-ink-muted">Themed from DESIGN.md</p>
          <Button variant="outline" size="sm" onClick={toggle}>
            {isDark ? "Light mode" : "Dark mode"}
          </Button>
        </div>
        <h1 className="type-display text-ink-strong max-w-4xl">
          GenBlocks design system
        </h1>
        <p className="type-subtitle text-ink-muted max-w-2xl">
          An editorial command center for a registry. White canvas, one
          monumental statement, coral taxonomy, and evidence you can read.
        </p>
        <nav className="border-hairline flex flex-wrap gap-x-6 gap-y-2 border-t pt-5">
          {ANCHORS.map(([id, label]) => (
            <a
              key={id}
              href={`#${id}`}
              className="type-label text-ink-muted hover:text-ink-strong"
            >
              {label}
            </a>
          ))}
        </nav>
      </header>

      <Section
        id="foundations"
        eyebrow="Foundations"
        title="Color, type, space, shape"
        lead="Roles first, palette second. Every surface is shown with its foreground and the contrast the browser actually measures."
      >
        <div className="flex flex-col gap-20">
          <Block label="Color roles">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {COLOR_PAIRS.map(([name, background, foreground]) => (
                <ColorPair
                  key={`${background}-${foreground}`}
                  name={name}
                  background={background}
                  foreground={foreground}
                />
              ))}
            </div>
          </Block>

          <div className="grid gap-16 lg:grid-cols-2">
            <Block label="Surfaces">
              <div className="grid grid-cols-2 gap-4">
                <Swatch token="canvas" name="Canvas" />
                <Swatch token="stone" name="Stone" />
                <Swatch token="stone-soft" name="Stone soft" />
                <Swatch token="wash-green" name="Wash green" />
                <Swatch token="wash-blue" name="Wash blue" />
                <Swatch token="hairline-soft" name="Hairline soft" />
              </div>
            </Block>

            <Block label="Ink and rules">
              <div className="grid grid-cols-2 gap-4">
                <Swatch token="ink-strong" name="Ink strong" />
                <Swatch token="ink" name="Ink" />
                <Swatch token="ink-muted" name="Ink muted" />
                <Swatch token="hairline" name="Hairline" />
              </div>
            </Block>

            <Block label="Accents">
              <div className="grid grid-cols-2 gap-4">
                <Swatch token="coral" name="Coral" />
                <Swatch token="coral-soft" name="Coral soft" />
                <Swatch token="link" name="Link" />
                <Swatch token="focus" name="Focus" />
              </div>
            </Block>

            <Block label="Bands and verdict">
              <div className="grid grid-cols-2 gap-4">
                <Swatch token="band" name="Band green" />
                <Swatch token="band-alt" name="Band navy" />
                <Swatch token="verdict-pass" name="Pass" />
                <Swatch token="verdict-fail" name="Fail" />
              </div>
            </Block>
          </div>

          <Block label="Typography">
            <div className="border-hairline overflow-hidden rounded-md border">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="bg-stone-soft border-hairline border-b">
                    <th className="type-label text-ink-muted px-4 py-3">
                      Token
                    </th>
                    <th className="type-label text-ink-muted px-4 py-3">
                      Spec
                    </th>
                    <th className="type-label text-ink-muted px-4 py-3">Use</th>
                    <th className="type-label text-ink-muted px-4 py-3">
                      Specimen
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {TYPE_ROWS.map(([utility, spec, use, sample]) => (
                    <tr
                      key={utility}
                      className="border-hairline border-b last:border-0"
                    >
                      <td className="type-mono text-ink px-4 py-3">
                        {utility}
                      </td>
                      <td className="type-mono text-ink-muted px-4 py-3">
                        {spec}
                      </td>
                      <td className="type-mono text-ink-muted px-4 py-3">
                        {use}
                      </td>
                      <td className="px-4 py-3">
                        <span className={`${utility} text-ink-strong`}>
                          {sample}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="type-body text-ink-muted mt-6 max-w-2xl">
              Three roles, and the split is the point:{" "}
              <strong className="text-ink-strong">Space Grotesk</strong> for the
              one declaration,{" "}
              <strong className="text-ink-strong">Hanken Grotesk</strong> for
              everything else,{" "}
              <strong className="text-ink-strong">Space Mono</strong> for data.
              Hierarchy comes from size and tracking, not weight — see the{" "}
              <a href="#rules" className="text-link underline">
                rules
              </a>
              .
            </p>
          </Block>

          <div className="grid gap-16 lg:grid-cols-2">
            <Block label="Spacing — 8px base">
              <div className="flex flex-col gap-3">
                {SPACING.map(([token, px, width]) => (
                  <div key={token} className="flex items-center gap-4">
                    <span className="type-mono text-ink-muted w-16">
                      {token}
                    </span>
                    <span className={`bg-ink h-3 ${width}`} />
                    <span className="type-mono text-ink-muted">{px}px</span>
                  </div>
                ))}
              </div>
            </Block>

            <Block label="Radius">
              <div className="flex flex-col gap-3">
                {RADIUS.map(([className, value, use]) => (
                  <div key={className} className="flex items-center gap-4">
                    <span
                      className={`border-hairline bg-stone size-12 shrink-0 border ${className}`}
                    />
                    <div className="flex flex-col">
                      <span className="type-mono text-ink">
                        {className} · {value}
                      </span>
                      <span className="type-mono text-ink-muted">{use}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Block>
          </div>

          <Block label="Elevation — flat">
            <div className="grid gap-6 sm:grid-cols-3">
              <div className="flex flex-col gap-3">
                <div className="border-hairline h-24 rounded-md border" />
                <span className="type-mono text-ink-muted">
                  flat · canvas, bands
                </span>
              </div>
              <div className="flex flex-col gap-3">
                <div className="border-hairline bg-stone h-24 rounded-md border" />
                <span className="type-mono text-ink-muted">
                  bordered · cards, forms, rows
                </span>
              </div>
              <div className="flex flex-col gap-3">
                <div className="border-hairline h-24 rounded-md border shadow-lg" />
                <span className="type-mono text-ink-muted">
                  overlay · dialogs, menus (the only shadow)
                </span>
              </div>
            </div>
          </Block>
        </div>
      </Section>

      <Section
        id="actions"
        eyebrow="Actions"
        title="Buttons and chips"
        lead="Primary CTAs are pills. Coral is taxonomy, so a chip is the only place a large coral area is allowed."
      >
        <div className="flex flex-col gap-14">
          <Block label="Variants">
            <div className="flex flex-wrap items-center gap-3">
              <Button>Generate component</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="destructive">Reject</Button>
              <Button variant="link">View trace</Button>
            </div>
          </Block>

          <Block label="Sizes">
            <div className="flex flex-wrap items-center gap-3">
              <Button size="xs">xs</Button>
              <Button size="sm">sm</Button>
              <Button>default</Button>
              <Button size="lg">lg</Button>
              <Button size="icon" aria-label="Generate">
                ✦
              </Button>
            </div>
          </Block>

          <Block label="States — pinned">
            <StateMatrix
              rows={["default", "outline", "secondary", "ghost"] as const}
              render={(row, state) => (
                <Button variant={row} {...previewState(state)}>
                  Button
                </Button>
              )}
            />
          </Block>

          <div className="grid gap-14 lg:grid-cols-2">
            <Block label="Category chips">
              <div className="flex flex-wrap items-center gap-3">
                <CategoryChip variant="active">Hero</CategoryChip>
                <CategoryChip>Pricing</CategoryChip>
                <CategoryChip variant="outline">Testimonials</CategoryChip>
                <CategoryChip size="sm">Features</CategoryChip>
              </div>
            </Block>
            <Block label="Verdict stamps and highlight">
              <div className="flex flex-wrap items-center gap-3">
                <VerdictStamp verdict="pass" />
                <VerdictStamp verdict="fail" />
              </div>
              <p className="type-body text-ink-muted mt-5">
                The run scored{" "}
                <Highlight>88 on the first threshold pass</Highlight>, so it
                shipped.
              </p>
            </Block>
          </div>
        </div>
      </Section>

      <Section
        id="inputs"
        eyebrow="Inputs"
        title="Fields"
        lead="Labels are uppercase mono; helper and error text are mono too. Control height is 44px."
      >
        <div className="grid gap-14 lg:grid-cols-2">
          <Block label="Typical">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="brief">Brief</FieldLabel>
                <Input
                  id="brief"
                  placeholder="A pricing table with three tiers"
                />
                <FieldDescription>
                  Describe the component; the agent decides the rest.
                </FieldDescription>
              </Field>
            </FieldGroup>
          </Block>

          <Block label="Error and disabled">
            <FieldGroup>
              <Field data-invalid>
                <FieldLabel htmlFor="slug">Slug</FieldLabel>
                <Input id="slug" aria-invalid defaultValue="pricing table" />
                <FieldError>Slugs use hyphens, not spaces.</FieldError>
              </Field>
              <Field data-disabled>
                <FieldLabel htmlFor="owner">Owner</FieldLabel>
                <Input id="owner" disabled defaultValue="genblocks" />
              </Field>
            </FieldGroup>
          </Block>

          <Block
            label="Label + input without a Field"
            className="lg:col-span-2"
          >
            <div className="flex max-w-sm flex-col gap-2">
              <Label htmlFor="plain">Plain label</Label>
              <Input
                id="plain"
                placeholder="Used when no helper text is needed"
              />
            </div>
          </Block>
        </div>
      </Section>

      <Section
        id="navigation"
        eyebrow="Navigation"
        title="Breadcrumb"
        lead="The registry gives every item a fixed address, so the trail is part of the layout."
      >
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink href="#">Components</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbLink href="#">Pricing</BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>№ 00217</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </Section>

      <Section
        id="data"
        eyebrow="Data display"
        title="Cards and rows"
        lead="Rows over cards. A card is for an object; a list of records is a rule-separated row, not a wall of tiles."
      >
        <div className="flex flex-col gap-14">
          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Pricing table</CardTitle>
                <CardDescription>
                  Three tiers, hairline rules, no drop shadow.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <p className="type-body text-ink-muted">
                  Surfaces step from canvas to stone and stop there. The
                  boundary is a 1px rule, not a shadow.
                </p>
                <Separator />
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback>GB</AvatarFallback>
                  </Avatar>
                  <span className="type-mono text-ink-muted">
                    generated by an agent · one run
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-stone">
              <CardHeader>
                <CardTitle>Score</CardTitle>
                <CardDescription>The run</CardDescription>
              </CardHeader>
              <CardContent>
                <ScoreReadout value={88} />
                <div className="mt-5 flex flex-wrap gap-2">
                  <CategoryChip size="sm">Pricing</CategoryChip>
                  <CategoryChip size="sm" variant="outline">
                    B2B
                  </CategoryChip>
                </div>
              </CardContent>
            </Card>
          </div>

          <Block label="Item">
            <div className="max-w-2xl">
              <Item variant="outline" className="rounded-md">
                <ItemMedia variant="icon">✦</ItemMedia>
                <ItemContent>
                  <ItemTitle>Hero with a split layout</ItemTitle>
                  <ItemDescription>
                    Passed every threshold · novelty 0.31
                  </ItemDescription>
                </ItemContent>
                <VerdictStamp verdict="pass" />
              </Item>
            </div>
          </Block>
        </div>
      </Section>

      <Section
        id="feedback"
        eyebrow="Feedback"
        title="Toasts"
        lead="Base UI toasts, on the one allowed shadow."
      >
        <Button
          variant="outline"
          onClick={() =>
            toast.add({
              title: "Component published",
              description: "№ 00217 is live with its scores.",
              type: "success",
            })
          }
        >
          Publish component
        </Button>
      </Section>

      <Section
        id="overlays"
        eyebrow="Overlays"
        title="Dialog, sheet, menu"
        lead="The only place a soft shadow is allowed. Everything else stays flat."
      >
        <div className="flex flex-wrap items-center gap-3">
          <Dialog>
            <DialogTrigger render={<Button variant="outline" />}>
              Open dialog
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Publish № 00217</DialogTitle>
                <DialogDescription>
                  Publishing is permanent. The score and the checks behind it
                  stay public.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <DialogClose render={<Button variant="secondary" />}>
                  Cancel
                </DialogClose>
                <Button>Publish</Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Sheet>
            <SheetTrigger render={<Button variant="outline" />}>
              Open sheet
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Task № 0041</SheetTitle>
                <SheetDescription>
                  spec → assets → harness → judge → commit
                </SheetDescription>
              </SheetHeader>
            </SheetContent>
          </Sheet>

          <DropdownMenu>
            <DropdownMenuTrigger render={<Button variant="outline" />}>
              Actions
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuLabel>Component</DropdownMenuLabel>
              <DropdownMenuItem>View trace</DropdownMenuItem>
              <DropdownMenuItem>Copy delivery prompt</DropdownMenuItem>
              <DropdownMenuItem>Create a variant</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem variant="destructive">Reject</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </Section>

      <Section
        id="bands"
        eyebrow="Bands"
        title="Evidence sections"
        lead="Where the system adds weight it changes the surface, not the shadow: full-width green or navy with white content."
      >
        <div className="flex flex-col gap-8">
          <DarkBand className="rounded-md px-8 py-12">
            <div className="flex flex-col gap-6">
              <p className="type-label opacity-70">Judge — the run</p>
              <div className="flex flex-wrap items-end justify-between gap-6">
                <h3 className="type-display-sm max-w-xl">
                  Passed every threshold it was held to.
                </h3>
                <ScoreReadout value={88} />
              </div>
              <ConsolePanel>
                {`spec → assets → harness → judge → commit`}
              </ConsolePanel>
            </div>
          </DarkBand>

          <DarkBand tone="navy" className="rounded-md px-8 py-12">
            <div className="flex flex-col gap-6">
              <p className="type-label opacity-70">Trace</p>
              <h3 className="type-display-sm max-w-xl">
                Every score stays visible, with the checks that earned it.
              </h3>
              <div className="bg-canvas rounded-md p-4">
                <ConsolePanel>{`scores · checks 9/9 · 2 files · one run`}</ConsolePanel>
              </div>
            </div>
          </DarkBand>
        </div>
      </Section>

      <Section
        id="rules"
        eyebrow="Do and Don’t"
        title="The rules, rendered"
        lead="Each pair is the DESIGN.md’s own guidance, shown rather than told."
      >
        <div className="flex flex-col gap-14">
          <Rule principle="Coral is taxonomy — never text on the canvas">
            <Correct>
              <div className="flex flex-wrap gap-2">
                <CategoryChip variant="active">Pricing</CategoryChip>
                <CategoryChip>Hero</CategoryChip>
              </div>
              <span className="type-mono text-ink-muted">
                coral as a chip fill with near-black text
              </span>
            </Correct>
            <Wrong>
              <p className="type-body text-coral">
                This is a coral paragraph on the canvas.
              </p>
              <span className="type-mono text-ink-muted">
                coral text measures 2.6:1 — it fails AA
              </span>
            </Wrong>
          </Rule>

          <Rule principle="Depth is a surface or a rule, not a shadow">
            <Correct>
              <div className="border-hairline h-20 rounded-md border" />
              <span className="type-mono text-ink-muted">1px hairline</span>
            </Correct>
            <Wrong>
              <div className="bg-stone h-20 rounded-4xl shadow-[0_20px_40px_rgba(23,23,28,0.28)]" />
              <span className="type-mono text-ink-muted">
                heavy shadow and an off-scale radius
              </span>
            </Wrong>
          </Rule>

          <Rule principle="Buttons are pills; hierarchy is size, not weight">
            <Correct>
              <div className="flex flex-wrap items-center gap-3">
                <Button>Generate</Button>
                <Button variant="outline">Cancel</Button>
              </div>
              <span className="type-mono text-ink-muted">
                400/500 weights, pill geometry
              </span>
            </Correct>
            <Wrong>
              <div className="flex flex-wrap items-center gap-3">
                <span className="type-body-sm bg-ink-strong inline-flex h-11 items-center rounded-sm px-6 font-bold text-white">
                  Generate
                </span>
                <span className="type-body-sm inline-flex h-11 items-center rounded-sm border border-black px-6 font-bold">
                  Cancel
                </span>
              </div>
              <span className="type-mono text-ink-muted">
                heavy weight and squared corners
              </span>
            </Wrong>
          </Rule>

          <Rule principle="Figures are tabular">
            <Correct>
              <div className="type-mono text-ink">
                <div className="tabular-nums">61.00</div>
                <div className="tabular-nums">78.40</div>
                <div className="tabular-nums">88.15</div>
              </div>
            </Correct>
            <Wrong>
              <div className="type-mono text-ink">
                <div>61.00</div>
                <div>78.4</div>
                <div>88.15</div>
              </div>
              <span className="type-mono text-ink-muted">
                ragged, proportional numerals
              </span>
            </Wrong>
          </Rule>
        </div>
      </Section>

      <Section
        id="recipe"
        eyebrow="Recipe"
        title="One item, composed"
        lead="Everything above, assembled the way the registry will show a component: specimen on the left, evidence on the right."
      >
        <Card>
          <CardHeader>
            <p className="type-label text-ink-muted">№ 00217 · Pricing</p>
            <CardTitle className="type-title">
              Three-tier pricing table
            </CardTitle>
            <CardDescription>
              Generated from the brief “a pricing table with three tiers”.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-10 lg:grid-cols-2">
            <div className="flex flex-col gap-5">
              <div className="flex flex-wrap gap-2">
                <CategoryChip size="sm" variant="active">
                  Pricing
                </CategoryChip>
                <CategoryChip size="sm">B2B</CategoryChip>
              </div>
              <p className="type-label text-ink-muted">Delivery prompt</p>
              <p className="type-body text-ink-muted">
                A pricing table for a developer tool: three tiers, the middle
                one
                <Highlight> featured</Highlight>, tabular figures throughout.
              </p>
              <ConsolePanel>{`<PricingTable featured="pro" />`}</ConsolePanel>
            </div>
            <div className="flex flex-col gap-6">
              <div className="flex items-start justify-between">
                <p className="type-label text-ink-muted">Judge — the run</p>
                <ScoreReadout value={88} />
              </div>
              <dl className="flex flex-col">
                {SCORES.map(([label, value]) => (
                  <div
                    key={label}
                    className="border-hairline flex items-baseline justify-between gap-6 border-t py-2.5"
                  >
                    <dt className="type-meta text-ink-muted">{label}</dt>
                    <dd>
                      <ScoreReadout value={value} />
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </CardContent>
        </Card>
      </Section>

      <footer className="border-hairline flex items-center justify-between border-t pt-6">
        <span className="type-label text-ink-muted">GenBlocks</span>
        <span className="type-mono text-ink-muted">
          Source of truth: DESIGN.md
        </span>
      </footer>
    </div>
  );
}

/* ------------------------------------------------------------- rule pairs */

function Rule({
  principle,
  children,
}: {
  principle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="border-hairline border-t pt-6">
      <p className="type-label text-ink-muted">{principle}</p>
      <div className="mt-5 grid gap-4 md:grid-cols-2">{children}</div>
    </div>
  );
}

function Correct({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-hairline flex flex-col gap-3 rounded-md border p-5">
      <span className="type-label text-verdict-pass">Do</span>
      {children}
    </div>
  );
}

function Wrong({ children }: { children: React.ReactNode }) {
  return (
    <div className="border-hairline flex flex-col gap-3 rounded-md border p-5">
      <span className="type-label text-verdict-fail">Don’t</span>
      {children}
    </div>
  );
}
