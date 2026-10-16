"use client"

import * as React from "react"

import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { AttemptLedger, type Attempt } from "@/components/ui/attempt-ledger"
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field"
import { Highlight } from "@/components/ui/highlight"
import { Input } from "@/components/ui/input"
import {
  Item,
  ItemContent,
  ItemDescription,
  ItemMedia,
  ItemTitle,
} from "@/components/ui/item"
import { Label } from "@/components/ui/label"
import { ScoreReadout } from "@/components/ui/score-readout"
import { Separator } from "@/components/ui/separator"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { toast } from "@/components/ui/toast"
import { VerdictStamp } from "@/components/ui/verdict-stamp"
import { useTheme } from "@/components/theme-toggle"
import { ColorPair } from "@/components/design-system/color-pair"
import {
  StateMatrix,
  previewState,
} from "@/components/design-system/state-matrix"

/* ------------------------------------------------------------------ layout */

const ANCHORS = [
  ["foundations", "Foundations"],
  ["actions", "Actions"],
  ["inputs", "Inputs"],
  ["navigation", "Navigation"],
  ["data", "Data display"],
  ["feedback", "Feedback"],
  ["overlays", "Overlays"],
  ["rules", "Do and Don’t"],
  ["recipe", "Recipe"],
] as const

function Section({
  id,
  eyebrow,
  title,
  lead,
  children,
}: {
  id: string
  eyebrow: string
  title: string
  lead?: string
  children: React.ReactNode
}) {
  return (
    <section id={id} className="scroll-mt-24">
      <header className="border-b border-rule-strong pb-4">
        <p className="type-label text-ink-faint">{eyebrow}</p>
        <h2 className="type-title mt-2 text-ink">{title}</h2>
        {lead ? (
          <p className="type-body-sm mt-2 max-w-2xl text-ink-soft">{lead}</p>
        ) : null}
      </header>
      <div className="mt-8">{children}</div>
    </section>
  )
}

function Block({
  label,
  children,
  className,
}: {
  label: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <div className={className}>
      <p className="type-label mb-4 text-ink-faint">{label}</p>
      {children}
    </div>
  )
}

/* -------------------------------------------------------------- foundations */

function Swatch({
  token,
  name,
  className,
}: {
  token: string
  name: string
  className?: string
}) {
  return (
    <div className="flex flex-col gap-2">
      <div
        className={`h-16 rounded-sm border border-rule ${className ?? ""}`}
        style={{ backgroundColor: `var(--${token})` }}
      />
      <div className="flex flex-col gap-0.5">
        <span className="type-body-sm text-ink">{name}</span>
        <span className="type-meta text-ink-faint">--{token}</span>
      </div>
    </div>
  )
}

const COLOR_PAIRS: Array<[string, string, string]> = [
  ["Page", "paper", "ink"],
  ["Card", "card", "card-foreground"],
  ["Popover", "popover", "popover-foreground"],
  ["Primary", "primary", "primary-foreground"],
  ["Secondary", "secondary", "secondary-foreground"],
  ["Muted", "muted", "muted-foreground"],
  ["Accent", "accent", "accent-foreground"],
  ["Error", "background", "destructive"],
  ["On-paper ink", "paper", "spot-secondary"],
  ["Pass", "verdict-pass-soft", "verdict-pass"],
  ["Retry", "verdict-retry-soft", "verdict-retry"],
  ["Fail", "verdict-fail-soft", "verdict-fail"],
]

const TYPE_ROWS: Array<[string, string, string, string]> = [
  ["type-display", "2.5rem · 600 · 1.05 · -0.02em", "Page titles", "Accession ledger"],
  ["type-title", "1.375rem · 600 · 1.25", "Section heads", "Attempt history"],
  ["type-body", "1rem · 400 · 1.55", "Running text", "Every component keeps its attempts."],
  ["type-body-sm", "0.875rem · 400 · 1.5", "Controls, dense copy", "Generate component"],
  ["type-label", "0.75rem · 700 · uppercase · 0.06em", "Eyebrows, labels", "Verdict"],
  ["type-meta", "0.8125rem · 400 · 1.4", "Metadata, tables", "№ 00217 · 2026-10-14"],
  ["type-code", "0.8125rem · 400 · 1.6", "Code, JSON", "const score = 88"],
  ["type-score", "1.75rem · 700 · tabular", "Judge score", "88"],
]

const SPACING: Array<[string, number, string]> = [
  ["xs", 4, "w-1"],
  ["sm", 8, "w-2"],
  ["md", 16, "w-4"],
  ["lg", 24, "w-6"],
  ["xl", 32, "w-8"],
  ["2xl", 48, "w-12"],
  ["3xl", 64, "w-16"],
  ["4xl", 96, "w-24"],
]

const RADIUS: Array<[string, string, string]> = [
  ["rounded-lg", "2px", "buttons, inputs, items"],
  ["rounded-md", "2px", "menu items"],
  ["rounded-xl", "4px", "cards, dialogs"],
  ["rounded-2xl", "6px", "toasts, large surfaces"],
  ["rounded-4xl", "2px", "badges (kept sharp — no pills)"],
]

/* -------------------------------------------------------------------- data */

const ATTEMPTS: Attempt[] = [
  { attempt: 1, timestamp: "2026-10-14 09:41", score: 61, verdict: "fail" },
  { attempt: 2, timestamp: "2026-10-14 09:58", score: 78, verdict: "retry" },
  { attempt: 3, timestamp: "2026-10-14 10:12", score: 88, verdict: "pass" },
]

/* -------------------------------------------------------------------- page */

export default function DesignSystemPage() {
  const { isDark, toggle } = useTheme()

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-24 px-6 py-16">
      {/* Header */}
      <header className="flex flex-col gap-8">
        <div className="flex items-center justify-between gap-4">
          <p className="type-label text-spot-secondary">Themed from DESIGN.md</p>
          <Button variant="outline" size="sm" onClick={toggle}>
            {isDark ? "Light mode" : "Dark mode"}
          </Button>
        </div>
        <h1 className="type-display max-w-3xl text-ink">
          GenBlocks design system
        </h1>
        <p className="type-body max-w-2xl text-ink-soft">
          Overprint — a risograph proof. Flat spot inks on bone paper, laid down
          one pass at a time. Color reports a verdict; it never decorates.
        </p>
        <nav className="flex flex-wrap gap-x-6 gap-y-2 border-t border-rule pt-4">
          {ANCHORS.map(([id, label]) => (
            <a key={id} href={`#${id}`} className="type-label text-ink-faint hover:text-ink">
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
        <div className="flex flex-col gap-16">
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

          <Block label="Palette — stock">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              <Swatch token="paper" name="Paper" />
              <Swatch token="panel" name="Panel" />
              <Swatch token="panel-sunken" name="Panel sunken" />
              <Swatch token="rule" name="Rule" />
              <Swatch token="rule-strong" name="Rule strong" />
              <Swatch token="ink" name="Ink" />
              <Swatch token="ink-soft" name="Ink soft" />
              <Swatch token="ink-faint" name="Ink faint" />
              <Swatch token="on-ink" name="On ink" />
            </div>
          </Block>

          <Block label="Palette — spot inks">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
              <Swatch token="spot-primary" name="Primary" />
              <Swatch token="spot-primary-hover" name="Primary hover" />
              <Swatch token="spot-secondary" name="Secondary" />
              <Swatch token="spot-accent" name="Accent" />
            </div>
          </Block>

          <Block label="Palette — verdict">
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
              <Swatch token="verdict-pass" name="Pass" />
              <Swatch token="verdict-pass-soft" name="Pass soft" />
              <Swatch token="verdict-retry" name="Retry" />
              <Swatch token="verdict-retry-soft" name="Retry soft" />
              <Swatch token="verdict-fail" name="Fail" />
              <Swatch token="verdict-fail-soft" name="Fail soft" />
            </div>
          </Block>

          <Block label="Typography">
            <div className="overflow-hidden rounded-md border border-rule">
              <table className="w-full border-collapse text-left">
                <thead>
                  <tr className="border-b border-rule-strong bg-panel-sunken">
                    <th className="type-label px-4 py-3 text-ink-faint">Token</th>
                    <th className="type-label px-4 py-3 text-ink-faint">Spec</th>
                    <th className="type-label px-4 py-3 text-ink-faint">Use</th>
                    <th className="type-label px-4 py-3 text-ink-faint">Specimen</th>
                  </tr>
                </thead>
                <tbody>
                  {TYPE_ROWS.map(([utility, spec, use, sample]) => (
                    <tr key={utility} className="border-b border-rule last:border-0">
                      <td className="type-meta px-4 py-3 text-ink">{utility}</td>
                      <td className="type-meta px-4 py-3 text-ink-soft">{spec}</td>
                      <td className="type-meta px-4 py-3 text-ink-soft">{use}</td>
                      <td className="px-4 py-3">
                        <span className={`${utility} text-ink`}>{sample}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="type-body mt-6 max-w-2xl text-ink-soft">
              Two families only: <strong className="text-ink">Bricolage Grotesque</strong>{" "}
              for voice and reading, <strong className="text-ink">Space Mono</strong> for
              everything that is data. Figures are always tabular, so columns of
              scores line up. Read more in the <a href="#recipe" className="text-spot-secondary underline">recipe</a>.
            </p>
          </Block>

          <div className="grid gap-16 lg:grid-cols-2">
            <Block label="Spacing — 4px base">
              <div className="flex flex-col gap-3">
                {SPACING.map(([token, px, width]) => (
                  <div key={token} className="flex items-center gap-4">
                    <span className="type-meta w-16 text-ink-faint">{token}</span>
                    <span className={`h-3 bg-ink ${width}`} />
                    <span className="type-meta text-ink-soft">{px}px</span>
                  </div>
                ))}
              </div>
            </Block>

            <Block label="Radius — capped at 6px">
              <div className="flex flex-col gap-3">
                {RADIUS.map(([className, value, use]) => (
                  <div key={className} className="flex items-center gap-4">
                    <span
                      className={`size-12 shrink-0 border border-rule bg-panel ${className}`}
                    />
                    <div className="flex flex-col">
                      <span className="type-meta text-ink">
                        {className} · {value}
                      </span>
                      <span className="type-meta text-ink-faint">{use}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Block>
          </div>

          <Block label="Elevation — hairline first">
            <div className="grid gap-6 sm:grid-cols-3">
              <div className="flex flex-col gap-3">
                <div className="h-24 rounded-md border border-rule bg-paper" />
                <span className="type-meta text-ink-soft">flat · canvas and bands</span>
              </div>
              <div className="flex flex-col gap-3">
                <div className="h-24 rounded-md border border-rule bg-panel" />
                <span className="type-meta text-ink-soft">hairline · cards, inputs</span>
              </div>
              <div className="flex flex-col gap-3">
                <div className="h-24 rounded-md border border-rule bg-panel shadow-lg" />
                <span className="type-meta text-ink-soft">overlay · dialogs, menus</span>
              </div>
            </div>
          </Block>
        </div>
      </Section>

      <Section
        id="actions"
        eyebrow="Actions"
        title="Buttons and stamps"
        lead="One primary action per view. The primary is a magenta block of ink with white text; never white on coral, never a pill."
      >
        <div className="flex flex-col gap-12">
          <Block label="Variants">
            <div className="flex flex-wrap items-center gap-3">
              <Button>Generate component</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="outline">Outline</Button>
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
              rows={["default", "secondary", "outline", "ghost"] as const}
              render={(row, state) => (
                <Button variant={row} {...previewState(state)}>
                  Button
                </Button>
              )}
            />
          </Block>

          <div className="grid gap-12 lg:grid-cols-2">
            <Block label="Verdict stamps">
              <div className="flex flex-wrap items-center gap-3">
                <VerdictStamp verdict="pass" />
                <VerdictStamp verdict="retry" />
                <VerdictStamp verdict="fail" />
              </div>
            </Block>
            <Block label="Highlight">
              <p className="type-body text-ink-soft">
                The winning attempt scored{" "}
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
        lead="Labels are uppercase mono; helper and error text are mono too. Control height is 40px across the board."
      >
        <div className="grid gap-12 lg:grid-cols-2">
          <Block label="Typical">
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="brief">Brief</FieldLabel>
                <Input id="brief" placeholder="A pricing table with three tiers" />
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

          <Block label="Label + input without a Field" className="lg:col-span-2">
            <div className="flex max-w-sm flex-col gap-2">
              <Label htmlFor="plain">Plain label</Label>
              <Input id="plain" placeholder="Used when no helper text is needed" />
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
        title="Cards, items, the ledger"
        lead="Cards are bordered cells, not floating tiles. The attempt ledger and the score readout are first-class surfaces — they are the product’s argument."
      >
        <div className="flex flex-col gap-12">
          <div className="grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Pricing table</CardTitle>
                <CardDescription>
                  Three tiers, hairline rules, no drop shadow.
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col gap-4">
                <p className="type-body text-ink-soft">
                  Card surfaces step up from paper to panel and stop there. The
                  boundary is a 1px rule, not a shadow.
                </p>
                <Separator />
                <div className="flex items-center gap-3">
                  <Avatar>
                    <AvatarFallback>GB</AvatarFallback>
                  </Avatar>
                  <span className="type-meta text-ink-soft">
                    generated by an agent · 3 attempts
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Score</CardTitle>
                <CardDescription>Last attempt</CardDescription>
              </CardHeader>
              <CardContent>
                <ScoreReadout value={88} />
              </CardContent>
            </Card>
          </div>

          <Block label="Item">
            <div className="max-w-xl">
              <Item variant="outline">
                <ItemMedia variant="icon">✦</ItemMedia>
                <ItemContent>
                  <ItemTitle>Hero with a split layout</ItemTitle>
                  <ItemDescription>
                    Passed on the first attempt · novelty 0.31
                  </ItemDescription>
                </ItemContent>
                <VerdictStamp verdict="pass" />
              </Item>
            </div>
          </Block>

          <Block label="Attempt ledger">
            <div className="max-w-2xl overflow-hidden rounded-md border border-rule">
              <AttemptLedger attempts={ATTEMPTS} />
            </div>
          </Block>
        </div>
      </Section>

      <Section
        id="feedback"
        eyebrow="Feedback"
        title="Toasts"
        lead="Base UI toasts. Fire one to see it; the surface carries the same hairline as everything else."
      >
        <Button
          variant="outline"
          onClick={() =>
            toast.add({
              title: "Component published",
              description: "№ 00217 is live with its attempt history.",
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
                  Publishing is permanent. The score and every attempt stay
                  public.
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
        id="rules"
        eyebrow="Do and Don’t"
        title="The rules, rendered"
        lead="Each pair is the DESIGN.md’s own guidance, shown rather than told."
      >
        <div className="flex flex-col gap-12">
          <Rule principle="Verdicts stay functional — never a brand ink">
            <Correct>
              <VerdictStamp verdict="fail" />
              <span className="type-meta text-ink-soft">
                Fail reads as failure, not as the primary action.
              </span>
            </Correct>
            <Wrong>
              <span className="type-label inline-flex w-fit items-center rounded-sm border border-primary/40 bg-primary/10 px-1.5 py-0.5 text-primary">
                REJECTED
              </span>
              <span className="type-meta text-ink-soft">
                A rejected component now looks like a call to action.
              </span>
            </Wrong>
          </Rule>

          <Rule principle="Depth is a rule or a tone step, not a shadow">
            <Correct>
              <div className="h-20 rounded-md border border-rule bg-panel" />
              <span className="type-meta text-ink-soft">1px hairline</span>
            </Correct>
            <Wrong>
              <div className="h-20 rounded-3xl bg-panel shadow-[0_20px_40px_rgba(23,21,15,0.28)]" />
              <span className="type-meta text-ink-soft">
                heavy drop shadow and an off-scale radius
              </span>
            </Wrong>
          </Rule>

          <Rule principle="One spot ink per screen">
            <Correct>
              <div className="flex flex-wrap items-center gap-3">
                <Button>Generate</Button>
                <Button variant="outline">Cancel</Button>
              </div>
              <span className="type-meta text-ink-soft">
                paper + ink + a single spot
              </span>
            </Correct>
            <Wrong>
              <div className="flex flex-wrap items-center gap-3">
                <Button>Magenta</Button>
                <span className="type-body-sm inline-flex h-10 items-center rounded-lg bg-spot-secondary px-2.5 font-medium text-on-spot">
                  Verdigris
                </span>
                <span className="type-body-sm inline-flex h-10 items-center rounded-lg bg-spot-accent px-2.5 font-medium text-on-accent">
                  Ochre
                </span>
              </div>
              <span className="type-meta text-ink-soft">
                three spot inks competing
              </span>
            </Wrong>
          </Rule>

          <Rule principle="Figures are tabular and aligned">
            <Correct>
              <div className="type-meta text-ink">
                <div className="tabular-nums">61.00</div>
                <div className="tabular-nums">78.40</div>
                <div className="tabular-nums">88.15</div>
              </div>
            </Correct>
            <Wrong>
              <div className="type-meta text-ink">
                <div>61.00</div>
                <div>78.4</div>
                <div>88.15</div>
              </div>
              <span className="type-meta text-ink-soft">
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
            <p className="type-label text-ink-faint">№ 00217 · Pricing</p>
            <CardTitle className="type-title">Three-tier pricing table</CardTitle>
            <CardDescription>
              Generated from the brief “a pricing table with three tiers”.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-8 lg:grid-cols-2">
            <div className="flex flex-col gap-4">
              <p className="type-label text-ink-faint">Delivery prompt</p>
              <p className="type-body text-ink-soft">
                A pricing table for a developer tool: three tiers, the middle one
                <Highlight> featured</Highlight>, tabular figures throughout.
              </p>
              <pre className="type-code overflow-x-auto rounded-sm border border-rule bg-panel-sunken p-4 text-ink">
                {`<PricingTable featured="pro" />`}
              </pre>
            </div>
            <div className="flex flex-col gap-6">
              <div className="flex items-start justify-between">
                <p className="type-label text-ink-faint">Judge — last attempt</p>
                <ScoreReadout value={88} />
              </div>
              <AttemptLedger attempts={ATTEMPTS} />
            </div>
          </CardContent>
        </Card>
      </Section>

      <footer className="flex items-center justify-between border-t border-rule pt-6">
        <span className="type-label text-ink-faint">GenBlocks · Overprint</span>
        <span className="type-meta text-ink-faint">
          Source of truth: DESIGN.md
        </span>
      </footer>
    </div>
  )
}

/* ------------------------------------------------------------- rule pairs */

function Rule({
  principle,
  children,
}: {
  principle: string
  children: React.ReactNode
}) {
  return (
    <div className="border-t border-rule pt-6">
      <p className="type-label text-ink-faint">{principle}</p>
      <div className="mt-4 grid gap-4 md:grid-cols-2">{children}</div>
    </div>
  )
}

function Correct({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-rule bg-panel p-4">
      <span className="type-label text-verdict-pass">Do</span>
      {children}
    </div>
  )
}

function Wrong({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-3 rounded-md border border-rule bg-panel p-4">
      <span className="type-label text-verdict-fail">Don’t</span>
      {children}
    </div>
  )
}
