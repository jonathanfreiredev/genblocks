/**
 * Where the MCP server lives, as seen from the page that documents it.
 *
 * The commands a client needs differ only in their URL: locally the server is
 * the compose service on port 8001, and in production it is the address the
 * deployment publishes. The page is rendered on the server, so the request's
 * Host header is enough to tell which one the reader is looking at — no build
 * flag and no second copy of the port in the client.
 */

/** The port `mcp` publishes in docker-compose.yml, and the one the README uses. */
export const LOCAL_MCP_PORT = 8001;

export type McpMode = "local" | "production";

export interface McpEndpoint {
  mode: McpMode;
  /**
   * The full endpoint, including `/mcp`. Null only when a production
   * deployment has not published one; the page says so rather than inventing a
   * URL that would fail on the first call.
   */
  endpoint: string | null;
}

/** The hostname of a Host header, without its port. IPv6 keeps its brackets. */
export function hostnameOf(host: string | null | undefined): string | null {
  if (!host) {
    return null;
  }

  try {
    return new URL(`http://${host}`).hostname;
  } catch {
    return null;
  }
}

// Addresses a laptop, a phone on the same network, or a compose container uses
// while the stack is being developed. Anything else is a deployment.
const PRIVATE_V4 = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;

/** Whether this request is being served from a development machine. */
export function isLocalHost(host: string | null | undefined): boolean {
  const hostname = hostnameOf(host);

  // No header is the one case that cannot be a public request: the page is
  // rendered per request precisely because it reads this.
  if (!hostname) {
    return true;
  }

  const bare = hostname.toLowerCase().replace(/^\[|\]$/g, "");

  return (
    bare === "localhost" ||
    bare === "::1" ||
    bare === "0.0.0.0" ||
    bare === "host.docker.internal" ||
    bare.endsWith(".local") ||
    bare.startsWith("127.") ||
    PRIVATE_V4.test(bare)
  );
}

/** The endpoint a client on this machine should use. */
export function localMcpEndpoint(host: string | null | undefined): string {
  const hostname = hostnameOf(host) ?? "localhost";

  return `http://${hostname}:${LOCAL_MCP_PORT}/mcp`;
}

/**
 * Read the configured public endpoint, accepting the base URL clients are often
 * given (`https://mcp.example.com`) as well as the full one.
 */
export function configuredMcpEndpoint(
  value: string | null | undefined,
): string | null {
  const trimmed = value?.trim().replace(/\/+$/, "");

  if (!trimmed) {
    return null;
  }

  return trimmed.endsWith("/mcp") ? trimmed : `${trimmed}/mcp`;
}

/** The mode the reader is in, and the endpoint that follows from it. */
export function resolveMcpEndpoint(
  host: string | null | undefined,
  configured: string | null | undefined,
): McpEndpoint {
  if (isLocalHost(host)) {
    return { mode: "local", endpoint: localMcpEndpoint(host) };
  }

  return {
    mode: "production",
    endpoint: configuredMcpEndpoint(configured),
  };
}
