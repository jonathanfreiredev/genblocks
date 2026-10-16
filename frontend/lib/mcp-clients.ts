/**
 * The MCP clients this project documents, and how each one is told where the
 * server is.
 *
 * Every value here comes from the client's own documentation, linked in `docs`.
 * Clients do not agree on the shape: some take a command, one takes a config
 * file, one is wired on a canvas. The landing renders this list, and the README
 * repeats the same content in prose.
 */
export type McpClient = {
  id: string;
  name: string;
  /** What the reader runs or pastes. */
  snippet: string;
  /** Accessible name for the copy button, since the snippet differs in kind. */
  copyLabel: string;
  /** Where the snippet goes, or what it is set on. */
  where: string;
  /** The step after, up to and including the consent screen. */
  next: string;
  /** The client's own MCP documentation. */
  docs: string;
};

export const MCP_CLIENTS: McpClient[] = [
  {
    id: "opencode",
    name: "opencode",
    snippet: "opencode mcp add mcp-stack --global --url http://localhost:8001/mcp",
    copyLabel: "Copy the command",
    where: "Run it in your terminal. Drop --global to register the server for this project only.",
    next: "Run /mcps, pick mcp-stack and sign in. opencode keeps the token from there on.",
    docs: "https://opencode.ai/v2/docs/mcp-servers",
  },
  {
    id: "claude-code",
    name: "Claude Code",
    snippet: "claude mcp add --transport http mcp-stack http://localhost:8001/mcp",
    copyLabel: "Copy the command",
    where: "Run it in your terminal, before you start Claude Code.",
    next: "Start Claude Code and run /mcp to sign in.",
    docs: "https://code.claude.com/docs/en/mcp",
  },
  {
    id: "cursor",
    name: "Cursor",
    snippet: [
      "{",
      '  "mcpServers": {',
      '    "mcp-stack": {',
      '      "url": "http://localhost:8001/mcp"',
      "    }",
      "  }",
      "}",
    ].join("\n"),
    copyLabel: "Copy the configuration",
    where: "Save it as .cursor/mcp.json in the project, or ~/.cursor/mcp.json to have it everywhere.",
    next: "Turn mcp-stack on in Cursor's MCP settings. It opens the browser to sign in.",
    docs: "https://cursor.com/en-US/docs/mcp",
  },
  {
    id: "n8n",
    name: "n8n",
    snippet: "http://localhost:8001/mcp",
    copyLabel: "Copy the URL",
    where: "Add an MCP Client Tool node under an AI Agent and paste that as its endpoint, with the transport set to HTTP Streamable, which is the one this server serves.",
    next: "For authentication pick OAuth2 and leave Dynamic Client Registration on. n8n registers itself and opens the same consent screen.",
    docs: "https://docs.n8n.io/integrations/builtin/cluster-nodes/sub-nodes/n8n-nodes-langchain.toolmcp/",
  },
];
