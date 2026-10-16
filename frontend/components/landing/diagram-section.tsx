import Image from "next/image";
import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { Section, SectionHeading } from "@/components/landing/section";

const BACKEND_README =
  "https://github.com/jonathanfreiredev/mcp-stack/blob/main/backend/README.md";

/**
 * Cloudinary resizes before the request leaves it, so the image optimizer
 * fetches a small file instead of the original 1.3 MB PNG.
 *
 * The alt text carries the diagram's own content: it is a bitmap, so the story
 * it tells has to survive as text somewhere.
 */
const DIAGRAM =
  "https://res.cloudinary.com/ddjovluur/image/upload/f_auto,q_auto,w_1086/v1791981836/mcp-stack/diagram-architecture_yo10gf.png";

const DIAGRAM_ALT =
  "Identity issuing one access token two ways, a frontend and external agents " +
  "such as Claude Code, Cursor, opencode or n8n, an MCP server, a FastAPI " +
  "backend and PostgreSQL, with the token carried along each path";

/**
 * The diagram, and what it means for whoever maintains the code.
 *
 * On a wide screen the picture sits on the left and the reading sits on the
 * right; on a phone the heading comes first, then the picture, then the reading.
 *
 * Nothing here is wrapped in an entrance animation: the picture is the reason
 * the section exists, and an animation that does not run would hide it.
 */
export function DiagramSection() {
  return (
    <Section>
      <SectionHeading title="Where an agent gets in" />

      <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] lg:gap-14">
        <figure>
          <Image
            src={DIAGRAM}
            alt={DIAGRAM_ALT}
            width={1086}
            height={1448}
            priority
            sizes="(min-width: 1024px) 610px, 100vw"
            className="border-border/70 w-full rounded-xl border bg-white"
          />

          <figcaption className="text-muted-foreground mt-3 text-sm">
            <Link
              href={DIAGRAM}
              target="_blank"
              rel="noreferrer"
              className="decoration-border hover:decoration-foreground inline-flex items-center gap-1 underline underline-offset-4 transition-[text-decoration-color]"
            >
              Open it full size
              <ArrowUpRight className="size-3.5" />
            </Link>
          </figcaption>
        </figure>

        <div className="text-muted-foreground max-w-[62ch] space-y-5 text-base text-pretty">
          <p>
            Your MCP server and your API run the same domain code. Publish a
            tool and an agent can do what that code allows, and no more.
          </p>
          <p>
            You write the logic once, and a claim on the access token decides
            which door answers it.
          </p>
          <p>
            <Link
              href={BACKEND_README}
              target="_blank"
              rel="noreferrer"
              className="decoration-border hover:decoration-foreground text-foreground inline-flex items-center gap-1 font-medium underline underline-offset-4 transition-[text-decoration-color]"
            >
              How the security model works
              <ArrowUpRight className="size-3.5" />
            </Link>
          </p>
        </div>
      </div>
    </Section>
  );
}
