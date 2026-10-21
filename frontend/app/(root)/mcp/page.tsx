import type { Metadata } from "next";
import { headers } from "next/headers";

import { ConnectAgent } from "@/components/mcp/connect-agent";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { env } from "@/lib/env";
import { resolveMcpEndpoint } from "@/lib/mcp";

export const metadata: Metadata = {
  title: "Connect an agent",
  description:
    "Point Claude Code, Cursor, opencode or n8n at the GenBlocks MCP server, and let an agent search, read and build in the same library this site shows.",
};

/**
 * How an agent reaches the vault.
 *
 * The page reads the request's Host header rather than a build flag: the same
 * build runs on a laptop and on the deployment, and only the endpoint changes.
 * A local request derives the development URL from the host it arrived on, so a
 * phone on the same network gets an address it can reach too.
 */
export default async function McpPage() {
  const headerList = await headers();
  // A proxy may rewrite Host and keep the reader's one here; either way, the
  // first value is the address the browser used.
  const host =
    headerList.get("x-forwarded-host")?.split(",")[0]?.trim() ||
    headerList.get("host");
  const { mode, endpoint } = resolveMcpEndpoint(host, env.MCP_URL);

  return (
    <div className="mx-auto w-full max-w-[900px] px-6 py-12">
      <h1 className="sr-only">Connect an agent</h1>

      <p className="text-muted-foreground max-w-[68ch] text-sm">
        GenBlocks speaks MCP, the protocol agent clients use to call tools.
        Point a client at the server once and it can search the library, read an
        item and queue a block or an image. The first call opens this
        site&apos;s consent screen, and the token that comes back can only reach
        those tools.
      </p>

      {endpoint ? (
        <ConnectAgent endpoint={endpoint} mode={mode} />
      ) : (
        <Alert className="mt-8">
          <AlertTitle>The public MCP endpoint is not configured</AlertTitle>
          <AlertDescription>
            This deployment has no published address yet, so there is nothing
            correct to put in a client command. Set <code>MCP_URL</code> to the
            URL clients should reach and reload this page.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
