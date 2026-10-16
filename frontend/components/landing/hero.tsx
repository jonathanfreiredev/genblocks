import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { CommandBlock } from "@/components/landing/command-block";
import { WakeNotice } from "@/components/demo/wake-notice";

const REPO = "https://github.com/jonathanfreiredev/mcp-stack";

/**
 * The offer, stated in one pass, with the action in the form a developer
 * actually takes it: the commands, ready to copy.
 */
export function Hero({ isSignedIn }: { isSignedIn: boolean }) {
  return (
    <section className="px-4 pt-[calc(var(--header-height)+4.5rem)] pb-24 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-5xl">
        <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          MCPStack
        </h1>

        <p className="text-muted-foreground mt-6 max-w-[62ch] text-lg text-pretty">
          The production-ready foundation for agent-native SaaS. Identity,
          permissions and the MCP server your agents talk to are already wired,
          so the first days go into your product.
        </p>

        <div className="mt-10 max-w-3xl">
          <CommandBlock />
          <p className="text-muted-foreground mt-3 text-sm text-pretty">
            Brings up Postgres, the API, the MCP server and the web app. Fill in
            your Supabase project to sign in.
          </p>
        </div>

        <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-3 text-sm">
          <Link
            href={REPO}
            target="_blank"
            rel="noreferrer"
            className="decoration-border hover:decoration-foreground inline-flex items-center gap-1 font-medium underline underline-offset-4 transition-[text-decoration-color]"
          >
            Read the code
            <ArrowUpRight className="size-3.5" />
          </Link>

          <Link
            href={isSignedIn ? "/profile" : "/auth/signup"}
            className="decoration-border hover:decoration-foreground text-muted-foreground hover:text-foreground inline-flex items-center gap-1 underline underline-offset-4 transition-colors"
          >
            {isSignedIn ? "Your profile" : "Create an account"}
          </Link>
        </div>

        {/* Sits under the actions so it is read at the point the visitor decides
            whether to try something, and takes no space at all when the demo is
            already up. */}
        <WakeNotice className="mt-8" />
      </div>
    </section>
  );
}
