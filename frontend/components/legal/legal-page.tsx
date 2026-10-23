import "server-only";

import { readFile } from "node:fs/promises";
import path from "node:path";

import { LegalMarkdown } from "@/components/legal/legal-markdown";

type LegalDocument = "imprint" | "privacy" | "terms";

/**
 * Where the Markdown lives, relative to the two roots the app can be started
 * from. Locally and in the container the project root is `frontend`; a build
 * that runs from the repository root needs the second path. Keeping both here
 * makes the route independent of which one the host chose.
 */
const LEGAL_DIRECTORIES = [
  path.join(process.cwd(), "content", "legal"),
  path.join(process.cwd(), "frontend", "content", "legal"),
];

async function readLegalSource(document: LegalDocument): Promise<string> {
  for (const directory of LEGAL_DIRECTORIES) {
    try {
      return await readFile(path.join(directory, `${document}.md`), "utf8");
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
        throw error;
      }
    }
  }

  throw new Error(
    `The legal document "${document}" is missing from the deployment.`,
  );
}

/**
 * A legal notice, rendered from the Markdown kept in `content/legal`.
 *
 * The text lives outside the component so it can be reviewed and edited as a
 * document. `next.config.ts` includes the files in the output trace for
 * deployments that run the page at request time.
 */
export async function LegalPage({ document }: { document: LegalDocument }) {
  const source = await readLegalSource(document);

  return (
    <main className="mx-auto w-full max-w-[68ch] px-3 py-10 md:px-4 md:py-14">
      <article className="legal-prose">
        <LegalMarkdown source={source} />
      </article>
    </main>
  );
}
