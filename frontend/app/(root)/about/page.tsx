import type { Metadata } from "next";
import Link from "next/link";

import { JsonLd, aboutPageJsonLd } from "@/lib/seo/json-ld";
import { pageMetadata } from "@/lib/seo/metadata";

const description =
  "What GenBlocks is, how a generated block or image reaches the registry, what the judge's scores mean, and how the work can be reused.";

export const metadata: Metadata = pageMetadata({
  title: "About the registry",
  description,
  path: "/about",
});

const link =
  "underline decoration-border underline-offset-4 transition-colors hover:text-muted-foreground hover:decoration-current";

export default function AboutPage() {
  return (
    <main className="mx-auto w-full max-w-[68ch] px-3 py-10 md:px-4 md:py-14">
      <JsonLd
        data={aboutPageJsonLd({
          name: "About GenBlocks",
          description,
        })}
      />

      <article className="text-base leading-7">
        <header>
          <p className="text-muted-foreground text-xs font-medium tracking-[0.05em] uppercase">
            About
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance">
            A public registry of generated work.
          </h1>
          <p className="text-muted-foreground mt-3 text-pretty">
            GenBlocks collects UI blocks and stock images made from prompts.
            Each published artifact carries what it looks like, what it was made
            from, and the scores of a judge that did not make it.
          </p>
        </header>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight">What this is</h2>
          <p className="mt-3 text-pretty">
            The catalogue is the product.{" "}
            <Link href="/blocks" className={link}>
              Blocks
            </Link>{" "}
            are React projects a visitor can preview, read and copy.{" "}
            <Link href="/images" className={link}>
              Images
            </Link>{" "}
            are stock assets with the prompt, the dimensions and the
            judge&apos;s evidence behind them. Nothing is filed privately: if it
            is here, it passed the gate.
          </p>
          <p className="mt-3 text-pretty">
            Browsing is free. Queueing work needs an account. If paid features
            are introduced later, the{" "}
            <Link href="/terms" className={link}>
              Terms
            </Link>{" "}
            will describe them; nothing here promises that every feature stays
            free forever.
          </p>
        </section>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight">
            How an artifact gets here
          </h2>
          <ol className="mt-3 list-decimal space-y-2 pl-5">
            <li>
              A person files a brief. It becomes one task, owned by that person.
            </li>
            <li>
              The harness builds the project in a sandbox and returns the
              render, the files and the checks it ran.
            </li>
            <li>
              An independent judge reads the result against a versioned rubric.
              It does not see the thresholds it has to clear.
            </li>
            <li>
              The item is published only when every dimension clears its bar. A
              run that fails stays a run, not a public artifact.
            </li>
          </ol>
        </section>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight">
            What the scores mean
          </h2>
          <p className="mt-3 text-pretty">
            The scores are the judge&apos;s reading of one artifact, not a user
            rating and not a promise that a block fits your product. The
            dimensions come from the rubric for that kind of work. A published
            item cleared every threshold; a number that looks low is still a
            number the gate accepted.
          </p>
        </section>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight">
            Provenance and reuse
          </h2>
          <p className="mt-3 text-pretty">
            Every block and image records the model, the prompt or brief, and
            the digital-source type that says it is AI-generated. Blocks are
            published under the MIT license unless the item says otherwise, so
            the code can be copied into a project. Images carry the license
            stated on the item. The evidence is part of the record: a copy
            should be able to say what it is.
          </p>
          <p className="mt-3 text-pretty">
            The{" "}
            <Link href="/terms" className={link}>
              Terms
            </Link>{" "}
            include the content policy. If something in the catalogue should not
            be there, use the report action on the item page.
          </p>
        </section>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight">Who runs it</h2>
          <p className="mt-3 text-pretty">
            GenBlocks is built and maintained by{" "}
            <a
              href="https://jonathanfreire.com"
              className={link}
              rel="noreferrer"
            >
              Jonathan Freire
            </a>{" "}
            in Berlin. The provider details, address and contact are in the{" "}
            <Link href="/impressum" className={link}>
              Impressum
            </Link>
            .
          </p>
        </section>

        <section className="mt-10">
          <h2 className="text-lg font-semibold tracking-tight">For agents</h2>
          <p className="mt-3 text-pretty">
            The same catalogue is available over MCP. An agent can search, read
            an item and queue work after the account holder approves the grant.{" "}
            <Link href="/mcp" className={link}>
              Connect an agent
            </Link>{" "}
            for the endpoint and the consent flow.
          </p>
        </section>

        <footer className="text-muted-foreground mt-12 border-t pt-4 text-xs">
          <time dateTime="2026-10-22">Last updated 22 October 2026.</time>
        </footer>
      </article>
    </main>
  );
}
