"""The development dataset: six blocks, six stock images and two tasks.

Planted by hand rather than generated, so the vault, the library and the task
drawer have something honest to show before the harness has run anything. The
blocks are the product's specimen — they are read by humans, so each one is real
TSX with its own rejected first pass beside it.

Every id is derived from a seed key, so the whole script is an upsert: a second
run rewrites the same rows instead of planting a second copy.

Run it with::

    python -m app.seed.vault
    python -m app.seed.vault --owner you@example.com

The taxonomy has to exist first; this raises and says so otherwise.
"""

import argparse
import asyncio
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.categories.models import Category
from app.components.models import DEFAULT_LICENSE, Component
from app.db.session import async_session_maker
from app.generations.models import Generation, Verdict
from app.harness.agent import ENTRY
from app.images.models import Image
from app.tasks.models import StepStatus, Task, TaskKind, TaskStatus, TaskStep
from app.users.models import User
from app.vectors import service as vectors

# The model and rubric the seeded attempts claim to have come from. Not a real
# run, so the trace id stays empty: there is nothing to replay.
COMPONENT_MODEL = "gpt-6-luna"
COMPONENT_RUBRIC_VERSION = "seed-v0"
IMAGE_MODEL = "flux-2-pro"
IMAGE_RUBRIC_VERSION = "seed-v0"

# Fixed timestamps: a re-run rewrites the same rows instead of drifting, and the
# task drawer reads as one morning of work rather than as "just now".
TASK_ONE_START = datetime(2026, 10, 2, 9, 12, tzinfo=UTC)
TASK_TWO_START = datetime(2026, 10, 2, 9, 40, tzinfo=UTC)


class SeedError(RuntimeError):
    """The dataset cannot be planted: something it depends on is missing."""


def _headline_score(scores: dict[str, int]) -> int:
    """The judge's headline number: the flat mean of its rubric scores."""
    return round(sum(scores.values()) / len(scores))


def _seed_id(key: str) -> uuid.UUID:
    """The deterministic id for a seeded row, so a re-run updates, never duplicates."""
    return uuid.uuid5(uuid.NAMESPACE_URL, f"genblocks/seed/{key}")


def _at(start: datetime, offset_seconds: int | None) -> datetime | None:
    return None if offset_seconds is None else start + timedelta(seconds=offset_seconds)


def _component_attempt_key(slug: str, attempt_no: int) -> str:
    return f"component/{slug}/attempt/{attempt_no}"


@dataclass(frozen=True)
class ComponentSpec:
    """One seeded block, its final attempt and the rejected pass before it.

    ``code`` is the block's single file as it is written here: the seed is
    authorship, not storage, and what it plants is a project with that file as
    its entry point.
    """

    slug: str
    category_slug: str
    title: str
    description: str
    delivery_prompt: str
    code: str
    rejected_code: str
    rejected_scores: dict[str, int]
    published_scores: dict[str, int]


@dataclass(frozen=True)
class ImageSpec:
    key: str
    path: str
    category_slug: str
    prompt: str
    width: int
    height: int
    scores: dict[str, int]


@dataclass(frozen=True)
class StepSpec:
    name: str
    status: str
    detail: dict | None = None
    # Offsets in seconds from the task's start; ``None`` means the step has not
    # got there yet.
    starts_at: int | None = None
    ends_at: int | None = None


@dataclass(frozen=True)
class TaskSpec:
    key: str
    brief: str
    status: str
    component_slug: str | None
    starts_at: datetime
    ends_at: datetime | None
    steps: tuple[StepSpec, ...]
    # A running task has an attempt before it has a component: this is the code
    # the judge has not seen yet.
    candidate_code: str | None = None


@dataclass(frozen=True)
class SeedSummary:
    components: int
    images: int
    tasks: int
    attempts: int
    owner_email: str | None
    indexed: int = 0


COMPONENTS: tuple[ComponentSpec, ...] = (
    ComponentSpec(
        slug="proof-sheet-hero",
        category_slug="hero",
        title="Proof-sheet hero",
        description=(
            "A left-aligned headline on a rule grid, with the primary action on the "
            "baseline of the last line and the supporting note in mono."
        ),
        delivery_prompt=(
            "Build a hero: a left-aligned display headline, one supporting line, and one "
            "primary action sitting on the baseline of the headline's last line, with a "
            "small mono note to the right of it. Rules instead of cards, nothing centred."
        ),
        code="""export function ProofSheetHero() {
  const ruler =
    "mt-16 flex flex-wrap items-baseline justify-between gap-6 border-t border-neutral-900 pt-5";
  const action =
    "rounded-sm bg-neutral-900 px-5 py-2.5 text-sm text-white hover:bg-neutral-800";

  return (
    <section
      aria-labelledby="proof-hero-title"
      className="bg-white px-6 py-24 text-neutral-900 sm:px-8 sm:py-32"
    >
      <div className="mx-auto max-w-5xl">
        <p className="font-mono text-xs font-bold uppercase tracking-[0.06em] text-neutral-500">
          Proof sheet · No. 001
        </p>

        <h1
          id="proof-hero-title"
          className="mt-10 font-sans text-4xl leading-[1.05] tracking-[-0.02em] sm:text-6xl"
        >
          Generated blocks,
          <span className="block">every attempt kept.</span>
        </h1>

        <div className={ruler}>
          <a href="/blocks" className={action}>
            Browse the vault
          </a>
          <p className="font-mono text-[0.8125rem] tabular-nums text-neutral-500">
            No sign-up · MIT licensed
          </p>
        </div>
      </div>
    </section>
  );
}
""",
        rejected_code="""export function Hero() {
  return (
    <section className="bg-white py-20 text-center">
      <div className="mx-auto max-w-3xl px-6">
        <h1 className="text-5xl font-bold text-slate-900">Welcome to our platform</h1>
        <p className="mt-4 text-lg text-slate-600">
          The best place to find components for your next project.
        </p>
        <a
          href="/blocks"
          className="mt-8 inline-block rounded-full bg-blue-600 px-8 py-3 text-white"
        >
          Get started
        </a>
        <div className="mt-12 grid grid-cols-3 gap-6 text-sm text-slate-500">
          <div>Fast</div>
          <div>Modern</div>
          <div>Reliable</div>
        </div>
      </div>
    </section>
  );
}
""",
        rejected_scores={
            "render": 90,
            "accessibility": 84,
            "visual": 61,
            "copy": 52,
            "novelty": 38,
            "compliance": 81,
        },
        published_scores={
            "render": 96,
            "accessibility": 94,
            "visual": 92,
            "copy": 89,
            "novelty": 88,
            "compliance": 97,
        },
    ),
    ComponentSpec(
        slug="tiered-pricing",
        category_slug="pricing",
        title="Tiered pricing",
        description=(
            "Three plans in a ruled table, the recommended tier marked in ink rather "
            "than colour, feature rows aligned across columns."
        ),
        delivery_prompt=(
            "Build a pricing section: three plans in one ruled table, feature rows aligned "
            "across the three columns, and the tier I want people to pick marked out in ink "
            "rather than with colour. No cards, no badges."
        ),
        code="""export function TieredPricing() {
  const label = "font-mono text-xs font-bold uppercase tracking-[0.06em] text-neutral-500";
  const head = "border-b border-neutral-400 px-4 py-4 align-bottom";
  const edge = "border-b border-neutral-200 px-4 py-3 text-center font-mono tabular-nums";
  const features = ["Blocks per month", "Attempt history kept", "Self-hosted export"];
  const feature = "bg-neutral-900 text-neutral-50";
  const plans = [
    { name: "Hobby", price: "$0", included: [true, true, false], header: "" },
    { name: "Team", price: "$24", included: [true, true, false], header: feature },
    { name: "Studio", price: "$60", included: [true, true, true], header: "" },
  ];

  return (
    <section
      aria-labelledby="pricing-title"
      className="mx-auto max-w-5xl bg-white px-6 py-20"
    >
      <h2 id="pricing-title" className="font-sans text-3xl">Three plans, one ledger</h2>

      <div className="mt-10 overflow-x-auto">
        <table className="w-full min-w-[34rem] border-collapse text-left text-sm">
          <caption className="sr-only">The three plans, feature by feature</caption>
          <thead>
            <tr>
              <th scope="col" className={`${head} pr-6 ${label}`}>Feature</th>
              {plans.map((plan) => (
                <th key={plan.name} scope="col" className={`${head} ${plan.header}`}>
                  <span className="block font-sans text-base">{plan.name}</span>
                  <span className="mt-2 block font-mono text-xl tabular-nums">{plan.price}</span>
                  {plan.header ? <span className={label}>Recommended</span> : null}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {features.map((feature, row) => (
              <tr key={feature} className={row % 2 === 1 ? "bg-neutral-100" : undefined}>
                <th scope="row" className="border-b border-neutral-200 py-3 pr-6 font-normal">
                  {feature}
                </th>
                {plans.map((plan) => (
                  <td className={plan.header ? `${edge} bg-white` : edge}>
                    {plan.included[row] ? "Included" : <span aria-hidden="true">—</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
""",
        rejected_code="""export function Pricing() {
  return (
    <section className="bg-gray-50 py-20">
      <h2 className="text-center text-4xl font-bold text-gray-900">Simple pricing</h2>
      <p className="mt-3 text-center text-gray-600">Start free, upgrade whenever you like.</p>
      <div className="mx-auto mt-10 grid max-w-5xl gap-6 px-6 md:grid-cols-3">
        <div className="rounded-2xl bg-white p-8 shadow-lg">
          <h3 className="text-lg font-semibold">Hobby</h3>
          <p className="mt-2 text-4xl font-bold">$0</p>
          <button className="mt-6 w-full rounded-full border py-2">Start free</button>
        </div>
        <div className="rounded-2xl bg-blue-600 p-8 text-white shadow-2xl">
          <span className="rounded-full bg-blue-500 px-3 py-1 text-xs">Most popular</span>
          <h3 className="mt-4 text-lg font-semibold">Team</h3>
          <p className="mt-2 text-4xl font-bold">$24</p>
          <button className="mt-6 w-full rounded-full bg-white py-2 text-blue-600">
            Choose Team
          </button>
        </div>
        <div className="rounded-2xl bg-white p-8 shadow-lg">
          <h3 className="text-lg font-semibold">Studio</h3>
          <p className="mt-2 text-4xl font-bold">$60</p>
          <button className="mt-6 w-full rounded-full border py-2">Talk to us</button>
        </div>
      </div>
    </section>
  );
}
""",
        rejected_scores={
            "render": 93,
            "accessibility": 87,
            "visual": 58,
            "copy": 44,
            "novelty": 35,
            "compliance": 82,
        },
        published_scores={
            "render": 95,
            "accessibility": 92,
            "visual": 90,
            "copy": 88,
            "novelty": 85,
            "compliance": 96,
        },
    ),
    ComponentSpec(
        slug="ops-dashboard",
        category_slug="dashboard",
        title="Ops dashboard",
        description=(
            "A stat band over a ruled activity table, with the range selector pinned "
            "to the header rule."
        ),
        delivery_prompt=(
            "Build an ops dashboard: a band of three figures across the top, over a ruled "
            "table of recent activity, with the range selector sitting on the header rule. "
            "Every number in mono and aligned in its column."
        ),
        code="""export function OpsDashboard() {
  const label = "font-mono text-xs font-bold uppercase tracking-[0.06em] text-neutral-500";
  const control = "rounded-sm border border-neutral-200 bg-white px-2 py-1 font-mono text-xs";
  const stats = { "Runs today": "1,284", "Pass rate": "72%", "Median attempt": "41s" };
  const activity = [
    { time: "14:02", block: "tiered-pricing", verdict: "published", tint: "text-emerald-700" },
    { time: "13:48", block: "proof-sheet-hero", verdict: "rejected", tint: "text-red-700" },
    { time: "13:31", block: "ruled-faq", verdict: "published", tint: "text-emerald-700" },
  ];

  return (
    <section
      aria-labelledby="ops-title"
      className="mx-auto max-w-5xl bg-white px-6 py-20 text-neutral-900"
    >
      <div className="flex items-end justify-between gap-4 border-b border-neutral-400 pb-3">
        <h2 id="ops-title" className="font-sans text-3xl">Pipeline</h2>
        <select aria-label="Range" className={control}>
          <option>Last 24 hours</option>
          <option>Last 7 days</option>
        </select>
      </div>
      <dl className="grid grid-cols-1 border-b border-neutral-200 sm:grid-cols-3">
        {Object.entries(stats).map(([name, value]) => (
          <div
            key={name}
            className="border-b border-neutral-200 py-6 sm:border-b-0 sm:border-r sm:pr-6"
          >
            <dt className={label}>{name}</dt>
            <dd className="mt-3 font-mono text-3xl font-bold tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>

      <table className="w-full border-collapse text-left text-sm">
        <caption className="sr-only">Runs in the selected range: time, block, verdict</caption>
        <thead>
          <tr>
            <th scope="col" className={`py-3 pr-6 ${label}`}>Time</th>
            <th scope="col" className={`py-3 pr-6 ${label}`}>Block</th>
            <th scope="col" className={`py-3 ${label}`}>Verdict</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-rule">
          {activity.map((row, index) => (
            <tr key={row.time} className={index % 2 === 1 ? "bg-neutral-100" : undefined}>
              <td className="py-3 pr-6 font-mono tabular-nums text-neutral-500">{row.time}</td>
              <td className="py-3 pr-6">{row.block}</td>
              <td className={`py-3 ${row.tint}`}>{row.verdict}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
""",
        rejected_code="""export function Dashboard() {
  const cards = [
    { label: "Runs", value: "1.3k" },
    { label: "Pass rate", value: "72%" },
    { label: "Latency", value: "41s" },
  ];

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="mx-auto max-w-6xl">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <div className="flex gap-2">
            <button className="rounded-md bg-gray-900 px-3 py-1 text-sm text-white">24h</button>
            <button className="rounded-md bg-white px-3 py-1 text-sm shadow">7d</button>
            <button className="rounded-md bg-white px-3 py-1 text-sm shadow">30d</button>
          </div>
        </div>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {cards.map((card) => (
            <div key={card.label} className="rounded-xl bg-white p-6 shadow-md">
              <p className="text-sm text-gray-500">{card.label}</p>
              <p className="mt-2 text-3xl font-bold text-gray-900">{card.value}</p>
            </div>
          ))}
        </div>
        <div className="mt-8 rounded-xl bg-white p-6 shadow-md">
          <p className="text-sm text-gray-500">Recent activity is listed in the table below.</p>
        </div>
      </div>
    </div>
  );
}
""",
        rejected_scores={
            "render": 88,
            "accessibility": 79,
            "visual": 56,
            "copy": 49,
            "novelty": 41,
            "compliance": 84,
        },
        published_scores={
            "render": 96,
            "accessibility": 91,
            "visual": 94,
            "copy": 87,
            "novelty": 92,
            "compliance": 95,
        },
    ),
    ComponentSpec(
        slug="margin-quotes",
        category_slug="testimonials",
        title="Margin quotes",
        description=(
            "Three quotes hung in the margin of one running column, each attributed "
            "in mono under a hairline."
        ),
        delivery_prompt=(
            "Build a quotes section: three quotes hung in the margin beside a single running "
            "column of text, each one attributed in mono under a hairline. No cards, no "
            "avatars, no star ratings."
        ),
        code="""export function MarginQuotes() {
  const quotes = [
    {
      text: "I stopped asking for a mockup. I type the brief and read the score sheet.",
      name: "Marisol Vega",
      role: "Design lead, Kestrel",
    },
    {
      text: "The rejected attempts are the useful part. They show where the brief was vague.",
      name: "Tobias Lund",
      role: "Staff engineer, Northgate",
    },
    {
      text: "We ship the block and keep the trace. Six months later we still know why.",
      name: "Rukmini Iyer",
      role: "Founder, Sable & Co",
    },
  ];

  return (
    <section
      aria-labelledby="margin-quotes-title"
      className="mx-auto max-w-5xl bg-white px-6 py-20 text-neutral-900"
    >
      <div className="grid gap-12 lg:grid-cols-[1fr_18rem] lg:gap-16">
        <div>
          <h2 id="margin-quotes-title" className="font-sans text-3xl">What the proof changed</h2>
          <p className="mt-6 max-w-[60ch] text-base leading-[1.55] text-neutral-600">
            A judge that only says yes is a rubber stamp. The ledger keeps the pass that
            failed on copy next to the one that shipped, so the brief sharpens with use.
          </p>
        </div>

        <ul className="space-y-8 lg:border-l lg:border-neutral-200 lg:pl-8">
          {quotes.map((quote) => (
            <li key={quote.name}>
              <figure className="leading-snug">
                <blockquote className="font-sans text-lg">“{quote.text}”</blockquote>
                <figcaption className="mt-3 border-t border-neutral-200 pt-3 font-mono text-xs">
                  {quote.name} · {quote.role}
                </figcaption>
              </figure>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
""",
        rejected_code="""export function Testimonials() {
  return (
    <section className="bg-white py-20">
      <h2 className="text-center text-4xl font-bold text-gray-900">Loved by teams everywhere</h2>
      <div className="mx-auto mt-12 grid max-w-5xl gap-8 px-6 md:grid-cols-3">
        {["Marisol Vega", "Tobias Lund", "Rukmini Iyer"].map((name) => (
          <div key={name} className="rounded-2xl border border-gray-200 p-6 shadow-sm">
            <div className="flex gap-1 text-yellow-500">★★★★★</div>
            <p className="mt-4 text-gray-600">
              “This tool completely transformed the way our team works.”
            </p>
            <div className="mt-6 flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gray-300" />
              <div>
                <p className="text-sm font-semibold text-gray-900">{name}</p>
                <p className="text-xs text-gray-500">Happy customer</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
""",
        rejected_scores={
            "render": 86,
            "accessibility": 82,
            "visual": 59,
            "copy": 47,
            "novelty": 44,
            "compliance": 80,
        },
        published_scores={
            "render": 93,
            "accessibility": 90,
            "visual": 91,
            "copy": 89,
            "novelty": 92,
            "compliance": 94,
        },
    ),
    ComponentSpec(
        slug="ruled-faq",
        category_slug="faq",
        title="Ruled FAQ",
        description=(
            "A single-column disclosure list where every question sits on its own "
            "hairline and opens in place."
        ),
        delivery_prompt=(
            "Build an FAQ: one column of disclosure rows, every question sitting on its own "
            "hairline and opening in place. No plus icons in circles, no cards, no accordion "
            "chrome."
        ),
        code="""export function RuledFaq() {
  const label = "font-mono text-xs font-bold uppercase tracking-[0.06em] text-neutral-500";
  const questions = [
    {
      q: "What exactly is an attempt?",
      a: "One pass of the generator: the code, the render, and the judge's six scores.",
    },
    {
      q: "Can I see the blocks that were rejected?",
      a: "Yes. Rejected attempts stay in the history, with the score that failed.",
    },
    {
      q: "What do I get when I copy a block?",
      a: "The TSX source, the delivery prompt, and the trace id to replay the brief.",
    },
  ];

  return (
    <section aria-labelledby="ruled-faq-title" className="mx-auto max-w-2xl bg-white px-6 py-20">
      <h2 id="ruled-faq-title" className={label}>Questions</h2>

      <div className="mt-6 border-t border-neutral-400">
        {questions.map((item) => (
          <details key={item.q} className="group border-b border-neutral-200">
            <summary className="flex cursor-pointer list-none justify-between py-5 text-lg">
              {item.q}
              <span aria-hidden="true" className="font-mono text-sm text-neutral-500">
                <span className="group-open:hidden">+</span>
                <span className="hidden group-open:inline">−</span>
              </span>
            </summary>
            <p className="max-w-[62ch] pb-6 text-sm text-neutral-600">{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
""",
        rejected_code="""export function Faq() {
  const items = [
    { q: "Is there a free plan?", a: "Yes, and it is generous." },
    { q: "Can I cancel?", a: "Of course, at any time." },
    { q: "Do you offer support?", a: "Our team is here to help." },
  ];

  return (
    <section className="bg-gray-50 py-20">
      <h2 className="text-center text-4xl font-bold text-gray-900">Frequently asked questions</h2>
      <div className="mx-auto mt-10 max-w-2xl px-6">
        {items.map((item) => (
          <div key={item.q} className="mb-4 rounded-xl bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">{item.q}</h3>
              <span className="text-xl text-gray-400">+</span>
            </div>
            <p className="mt-2 text-sm text-gray-600">{item.a}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
""",
        rejected_scores={
            "render": 94,
            "accessibility": 86,
            "visual": 63,
            "copy": 55,
            "novelty": 39,
            "compliance": 83,
        },
        published_scores={
            "render": 97,
            "accessibility": 96,
            "visual": 93,
            "copy": 92,
            "novelty": 90,
            "compliance": 98,
        },
    ),
    ComponentSpec(
        slug="closing-band",
        category_slug="cta",
        title="Closing band",
        description=(
            "An ink band that closes a page: one action, one mono footnote, generous space."
        ),
        delivery_prompt=(
            "Build a closing band for the end of a page: a solid ink strip with one headline, "
            "one action and a small mono footnote, and a lot of air around them. Nothing "
            "centred, no illustration."
        ),
        code="""export function ClosingBand() {
  return (
    <section
      aria-labelledby="closing-band-title"
      className="bg-neutral-900 px-6 py-24 text-neutral-50"
    >
      <div className="mx-auto flex max-w-4xl flex-col items-start gap-10">
        <h2
          id="closing-band-title"
          className="max-w-xl font-sans text-3xl leading-tight sm:text-4xl"
        >
          Write the brief. Keep the proof.
        </h2>

        <a
          href="/start"
          className="rounded-sm bg-amber-200 px-6 py-3 text-sm text-amber-950"
        >
          Start with a brief
        </a>

        <p className="font-mono text-[0.8125rem] tabular-nums text-neutral-400">
          No card · first twenty blocks free · cancel any time
        </p>
      </div>
    </section>
  );
}
""",
        rejected_code="""export function Cta() {
  return (
    <section className="bg-indigo-600 py-24 text-center">
      <div className="mx-auto max-w-3xl px-6">
        <h2 className="text-4xl font-bold text-white">Ready to get started?</h2>
        <p className="mt-4 text-indigo-100">
          Join thousands of teams already building faster than ever before.
        </p>
        <div className="mt-8 flex justify-center gap-4">
          <a href="/start" className="rounded-full bg-white px-8 py-3 text-indigo-600">
            Get started free
          </a>
          <a href="/pricing" className="rounded-full border border-white/40 px-8 py-3 text-white">
            Book a demo
          </a>
        </div>
      </div>
    </section>
  );
}
""",
        rejected_scores={
            "render": 85,
            "accessibility": 78,
            "visual": 60,
            "copy": 45,
            "novelty": 37,
            "compliance": 86,
        },
        published_scores={
            "render": 92,
            "accessibility": 89,
            "visual": 90,
            "copy": 91,
            "novelty": 87,
            "compliance": 95,
        },
    ),
)

IMAGES: tuple[ImageSpec, ...] = (
    ImageSpec(
        key="bench-at-dusk",
        path="genblocks/images/bench-at-dusk",
        category_slug="photography",
        prompt=(
            "A workshop bench at dusk under a single desk lamp, hand tools in order along "
            "the edge, shallow depth of field"
        ),
        width=1536,
        height=1024,
        scores={"visual": 94, "prompt_fit": 91, "compliance": 97},
    ),
    ImageSpec(
        key="verdigris-bleed",
        path="genblocks/images/verdigris-bleed",
        category_slug="abstract-background",
        prompt=(
            "Deep verdigris ink bleeding into bone paper, one pass, hard edges, visible "
            "halftone grain"
        ),
        width=1536,
        height=1024,
        scores={"visual": 96, "prompt_fit": 88, "compliance": 93},
    ),
    ImageSpec(
        key="register-screen",
        path="genblocks/images/register-screen",
        category_slug="product-mockup",
        prompt=(
            "A browser window on a bare off-white desk, screen showing a ruled data table, "
            "no logos, soft daylight"
        ),
        width=1536,
        height=1024,
        scores={"visual": 90, "prompt_fit": 95, "compliance": 92},
    ),
    ImageSpec(
        key="halftone-stock",
        path="genblocks/images/halftone-stock",
        category_slug="texture-pattern",
        prompt="A coarse halftone dot field in black over warm bone paper, even coverage",
        width=1024,
        height=1024,
        scores={"visual": 92, "prompt_fit": 89, "compliance": 96},
    ),
    ImageSpec(
        key="three-boxes",
        path="genblocks/images/three-boxes",
        category_slug="illustration",
        prompt=(
            "A flat two-colour line diagram of three labelled boxes joined by arrows, on "
            "paper, no lettering"
        ),
        width=1536,
        height=1024,
        scores={"visual": 87, "prompt_fit": 93, "compliance": 90},
    ),
    ImageSpec(
        key="stone-harbour",
        path="genblocks/images/stone-harbour",
        category_slug="scene",
        # The prompt is verbatim, so the line cannot be split.
        prompt="A small stone harbour at dawn, still water, one moored boat, low cloud, muted palette",  # noqa: E501
        width=1536,
        height=1024,
        scores={"visual": 95, "prompt_fit": 92, "compliance": 94},
    ),
)

# The judge's headline score, shown beside the verdict: the flat mean of the six
# rubric scores. Kept here rather than written out by hand, so the task drawer
# can never disagree with the attempt it is describing.
COMPONENTS_BY_SLUG = {spec.slug: spec for spec in COMPONENTS}

# The checklists below mirror the one the runner writes (``app.tasks.runner``):
# the same step names, in the same order, so a seeded task and a task that
# actually ran read the same way. The moderation line is the one step no runner
# writes yet; it arrives with moderation (Fase 11).
TASKS: tuple[TaskSpec, ...] = (
    TaskSpec(
        key="pricing-page-brief",
        brief=(
            "A pricing page for a developer tool, three tiers, with an annual toggle and "
            "a comparison row per feature."
        ),
        status=TaskStatus.SUCCEEDED,
        component_slug="tiered-pricing",
        starts_at=TASK_ONE_START,
        ends_at=TASK_ONE_START + timedelta(seconds=47),
        steps=(
            StepSpec(
                name="Moderating the brief",
                status=StepStatus.SUCCEEDED,
                detail={"outcome": "accepted", "flags": 0},
                starts_at=0,
                ends_at=3,
            ),
            StepSpec(
                name="Retrieving references",
                status=StepStatus.SUCCEEDED,
                detail={"references": 4},
                starts_at=3,
                ends_at=6,
            ),
            StepSpec(
                name="Generating the block",
                status=StepStatus.SUCCEEDED,
                detail={"attempts": 2},
                starts_at=6,
                ends_at=41,
            ),
            StepSpec(
                name="Judging the attempt",
                status=StepStatus.SUCCEEDED,
                detail={
                    "verdict": "published",
                    "score": _headline_score(COMPONENTS_BY_SLUG["tiered-pricing"].published_scores),
                },
                starts_at=41,
                ends_at=45,
            ),
            StepSpec(
                name="Publishing the block",
                status=StepStatus.SUCCEEDED,
                detail={"slug": "tiered-pricing"},
                starts_at=45,
                ends_at=47,
            ),
        ),
    ),
    TaskSpec(
        key="changelog-page-brief",
        brief=(
            "A changelog page for a design system, dated entries with an author and a "
            "small tag per entry."
        ),
        status=TaskStatus.RUNNING,
        component_slug=None,
        starts_at=TASK_TWO_START,
        ends_at=None,
        steps=(
            StepSpec(
                name="Moderating the brief",
                status=StepStatus.SUCCEEDED,
                detail={"outcome": "accepted", "flags": 0},
                starts_at=0,
                ends_at=4,
            ),
            StepSpec(
                name="Retrieving references",
                status=StepStatus.SUCCEEDED,
                detail={"references": 3},
                starts_at=4,
                ends_at=7,
            ),
            StepSpec(
                name="Generating the block",
                status=StepStatus.RUNNING,
                detail={"attempts": 1},
                starts_at=7,
            ),
            StepSpec(name="Judging the attempt", status=StepStatus.PENDING),
        ),
        candidate_code="""export function ChangelogList() {
  const entries = [
    { date: "18 Sep", title: "Tabular numerals by default", author: "Marisol Vega", tag: "tokens" },
    { date: "09 Sep", title: "Rule colour passes AA on panel", author: "Tobias Lund", tag: "fix" },
  ];

  return (
    <section className="mx-auto max-w-2xl px-6 py-16">
      <h2 className="font-sans text-3xl">Changelog</h2>
      <ul className="mt-8 border-t border-neutral-400">
        {entries.map((entry) => (
          <li key={entry.date} className="border-b border-neutral-200 py-6">
            <div className="flex items-baseline justify-between font-mono text-xs text-neutral-500">
              <time>{entry.date}</time>
              <span>{entry.tag}</span>
            </div>
            <p className="mt-2 font-sans text-lg">{entry.title}</p>
            <p className="mt-1 text-sm text-neutral-600">{entry.author}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
""",
    ),
)


async def seed_vault(session: AsyncSession, *, owner_email: str | None = None) -> SeedSummary:
    """Plant the dataset, keyed by deterministic id, and return what was written.

    Idempotent: a second run rewrites the same rows. The taxonomy is read, never
    planted here — a missing category is an error, not something to invent.
    """
    owner_id = await _resolve_owner(session, owner_email=owner_email)
    categories = await _load_categories(session, slugs=_category_slugs())

    components = await _seed_components(session, categories=categories)
    attempts = await _seed_component_attempts(session, components=components)
    attempts += await _seed_tasks(session, components=components, owner_id=owner_id)

    images = await _seed_images(session, categories=categories)

    await session.commit()

    # Retrieval is built after the rows are, and from what the rows say: the
    # seeded blocks have no render and the seeded pictures no bytes, so they are
    # remembered by their words. A registry that cannot be searched in
    # development is a feature nobody can try.
    indexed = await _seed_vectors(components=components, images=images, categories=categories)

    return SeedSummary(
        components=len(COMPONENTS),
        images=len(IMAGES),
        tasks=len(TASKS),
        attempts=attempts,
        owner_email=owner_email,
        indexed=indexed,
    )


async def _seed_vectors(
    *,
    components: dict[str, Component],
    images: list[Image],
    categories: dict[str, Category],
) -> int:
    """Remember the seeded rows as vectors, by their words.

    Best effort on purpose: a development database has to be seedable without the
    embedder, and the seed says how many it managed to remember rather than
    failing over a network it does not control.
    """
    slug_of = {category.id: slug for slug, category in categories.items()}

    remembered = await vectors.remember_component_texts(
        entries=[
            (
                component.id,
                f"{component.title}. {component.description}\n\n{component.delivery_prompt}",
                component.slug,
                slug_of.get(component.category_id, ""),
            )
            for component in components.values()
        ]
    )
    remembered += await vectors.remember_image_texts(
        entries=[(image.id, image.prompt, slug_of.get(image.category_id, "")) for image in images]
    )

    return remembered


async def _resolve_owner(session: AsyncSession, *, owner_email: str | None) -> uuid.UUID | None:
    """The id of the user the tasks belong to, or ``None`` for unowned tasks.

    A domain row only exists here after the account has signed in once, so an
    unknown email is a mistake worth naming rather than a task planted against
    nobody.
    """
    if owner_email is None:
        return None

    user = await session.scalar(select(User).where(User.email == owner_email))
    if user is None:
        raise SeedError(
            f"No user with the email {owner_email!r}. The account has to sign in once "
            "before a profile exists here; sign in, then run the seed again."
        )

    return user.id


def _category_slugs() -> set[str]:
    return {spec.category_slug for spec in COMPONENTS} | {spec.category_slug for spec in IMAGES}


async def _load_categories(session: AsyncSession, *, slugs: set[str]) -> dict[str, Category]:
    """Look the categories up by slug, refusing to plant a component without one."""
    categories = {
        category.slug: category
        for category in await session.scalars(select(Category).where(Category.slug.in_(slugs)))
    }

    if missing := sorted(slugs - set(categories)):
        raise SeedError(
            f"Missing categories: {', '.join(missing)}. Run `python -m app.categories.seed` first."
        )

    return categories


async def _seed_components(
    session: AsyncSession, *, categories: dict[str, Category]
) -> dict[str, Component]:
    """Upsert the blocks themselves and return them keyed by slug.

    The winner is written in a second pass: ``winning_generation_id`` points at a
    row the attempts create, so the block has to exist first.
    """
    components: dict[str, Component] = {}

    for spec in COMPONENTS:
        component_id = _seed_id(f"component/{spec.slug}")
        component = await session.get(Component, component_id)
        if component is None:
            component = Component(id=component_id, slug=spec.slug)
            session.add(component)

        component.title = spec.title
        component.description = spec.description
        component.category_id = categories[spec.category_slug].id
        component.files = {ENTRY: spec.code}
        component.entry = ENTRY
        component.delivery_prompt = spec.delivery_prompt
        component.spec = None
        component.provenance = {
            "digital_source_type": "trainedAlgorithmicMedia",
            "kind": "component",
            "model": "seed",
        }
        component.license = DEFAULT_LICENSE
        component.created_by = None
        components[spec.slug] = component

    await session.flush()
    return components


async def _seed_component_attempts(
    session: AsyncSession, *, components: dict[str, Component]
) -> int:
    """Upsert two attempts per block and point each block at its second one."""
    for spec in COMPONENTS:
        component = components[spec.slug]
        attempts = (
            (1, Verdict.REJECTED, spec.rejected_code, spec.rejected_scores),
            (2, Verdict.PUBLISHED, spec.code, spec.published_scores),
        )

        for attempt_no, verdict, code, scores in attempts:
            generation_id = _seed_id(_component_attempt_key(spec.slug, attempt_no))
            generation = await session.get(Generation, generation_id)
            if generation is None:
                generation = Generation(id=generation_id, attempt_no=attempt_no)
                session.add(generation)

            # No task behind a seeded attempt: it stands on its own, which is the
            # case the schema explicitly allows.
            generation.task_id = None
            generation.component_id = component.id
            generation.attempt_no = attempt_no
            generation.files = {ENTRY: code}
            generation.entry = ENTRY
            # The render and the checks are deliberately not reset: a screenshot
            # costs a container and a cloud upload, and re-seeding is a reset of
            # the text, not of the artifacts that were captured.
            generation.scores = scores
            generation.verdict = verdict
            generation.rubric_version = COMPONENT_RUBRIC_VERSION
            generation.model = COMPONENT_MODEL
            generation.langfuse_trace_id = None

    # Flushed before the winners are assigned: the two tables point at each other
    # (``use_alter``), so Postgres cannot check the block's pointer until the
    # attempts are actually in the table.
    await session.flush()

    for spec in COMPONENTS:
        components[spec.slug].winning_generation_id = _seed_id(_component_attempt_key(spec.slug, 2))

    await session.flush()
    return 2 * len(COMPONENTS)


async def _seed_tasks(
    session: AsyncSession,
    *,
    components: dict[str, Component],
    owner_id: uuid.UUID | None,
) -> int:
    """Upsert the tasks, their checklists and any attempt they have made.

    One task is finished and produced a block; the other is mid-flight, with an
    attempt that has no component yet.
    """
    for spec in TASKS:
        task_id = _seed_id(f"task/{spec.key}")
        task = await session.get(Task, task_id)
        if task is None:
            task = Task(id=task_id, brief=spec.brief)
            session.add(task)

        task.kind = TaskKind.GENERATE_COMPONENT
        task.status = spec.status
        task.brief = spec.brief
        task.component_id = components[spec.component_slug].id if spec.component_slug else None
        task.created_by = owner_id
        task.created_at = spec.starts_at
        task.finished_at = spec.ends_at
        task.error = None
        task.langfuse_trace_id = None
        await session.flush()

        for index, step_spec in enumerate(spec.steps):
            step_id = _seed_id(f"task/{spec.key}/step/{index}")
            step = await session.get(TaskStep, step_id)
            if step is None:
                step = TaskStep(id=step_id, task_id=task.id, index=index, name=step_spec.name)
                session.add(step)

            step.task_id = task.id
            step.index = index
            step.name = step_spec.name
            step.status = step_spec.status
            step.detail = step_spec.detail
            step.started_at = _at(spec.starts_at, step_spec.starts_at)
            step.finished_at = _at(spec.starts_at, step_spec.ends_at)

        if spec.candidate_code is not None:
            await _seed_candidate_attempt(session, spec=spec, task_id=task.id)

    await session.flush()
    return len([spec for spec in TASKS if spec.candidate_code is not None])


async def _seed_candidate_attempt(
    session: AsyncSession, *, spec: TaskSpec, task_id: uuid.UUID
) -> None:
    """Upsert the one attempt of a running task: scored by nobody yet."""
    generation_id = _seed_id(f"task/{spec.key}/attempt/1")
    generation = await session.get(Generation, generation_id)
    if generation is None:
        generation = Generation(id=generation_id, attempt_no=1)
        session.add(generation)

    generation.task_id = task_id
    generation.component_id = None
    generation.attempt_no = 1
    generation.files = {ENTRY: spec.candidate_code}
    generation.entry = ENTRY
    generation.scores = None
    generation.verdict = Verdict.CANDIDATE
    generation.rubric_version = None
    generation.model = COMPONENT_MODEL
    generation.langfuse_trace_id = None


async def _seed_images(session: AsyncSession, *, categories: dict[str, Category]) -> list[Image]:
    """Upsert the stock images and the generation panel that produced each one."""
    planted: list[Image] = []

    for spec in IMAGES:
        image_id = _seed_id(f"image/{spec.key}")
        image = await session.get(Image, image_id)
        if image is None:
            # The path is the asset's public id. Once a generated picture has
            # replaced the seed's readable placeholder, re-seeding keeps the real
            # one: the bytes were paid for and the row already points at them.
            image = Image(id=image_id, path=spec.path)
            session.add(image)

        image.slug = spec.key
        image.prompt = spec.prompt
        image.width = spec.width
        image.height = spec.height
        image.category_id = categories[spec.category_slug].id
        image.created_by = None
        image.license = DEFAULT_LICENSE
        image.model = IMAGE_MODEL
        image.scores = spec.scores
        image.rubric_version = IMAGE_RUBRIC_VERSION
        image.langfuse_trace_id = None
        image.provenance = {
            "digital_source_type": "trainedAlgorithmicMedia",
            "kind": "image",
            "model": IMAGE_MODEL,
        }
        planted.append(image)

    await session.flush()

    return planted


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plant the GenBlocks development dataset.")
    parser.add_argument(
        "--owner",
        metavar="EMAIL",
        default=None,
        help="Attach the seeded tasks to this user (the account must have signed in once).",
    )
    return parser.parse_args(argv)


async def _run(owner_email: str | None) -> SeedSummary:
    async with async_session_maker() as session:
        return await seed_vault(session, owner_email=owner_email)


def _main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    try:
        summary = asyncio.run(_run(args.owner))
    except SeedError as error:
        print(f"Seed failed: {error}")
        raise SystemExit(1) from error

    print(
        f"Seeded {summary.components} components, {summary.images} images, "
        f"{summary.tasks} tasks and {summary.attempts} attempts"
    )
    print(f"Remembered {summary.indexed} rows as vectors")
    if summary.owner_email is None:
        print(
            "The tasks are unowned: no --owner was given, so no account can see them.\n"
            "Sign in once, then re-run with the address you signed in with:\n"
            "  python -m app.seed.vault --owner you@example.com"
        )
    else:
        print(f"The tasks belong to {summary.owner_email}.")


if __name__ == "__main__":
    _main()
