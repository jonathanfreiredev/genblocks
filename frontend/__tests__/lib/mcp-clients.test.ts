import { describe, expect, test } from "vitest";

import { mcpClients } from "@/lib/mcp-clients";

const ENDPOINT = "http://localhost:8001/mcp";

describe("mcpClients", () => {
  test("documents one shape per client", () => {
    expect(mcpClients(ENDPOINT).map((client) => client.id)).toEqual([
      "opencode",
      "claude-code",
      "cursor",
      "n8n",
    ]);
  });

  test("writes the endpoint into every snippet", () => {
    for (const client of mcpClients(ENDPOINT)) {
      expect(client.snippet).toContain(ENDPOINT);
    }
  });

  test("gives Cursor a file that parses to the same server", () => {
    const cursor = mcpClients(ENDPOINT).find(
      (client) => client.id === "cursor",
    );

    expect(cursor).toBeDefined();
    expect(JSON.parse(cursor!.snippet)).toEqual({
      mcpServers: { genblocks: { url: ENDPOINT } },
    });
  });

  test("changes nothing but the URL when the server moves", () => {
    const local = mcpClients(ENDPOINT);
    const deployed = mcpClients("https://mcp.example.com/mcp");

    expect(deployed.map((client) => client.snippet)).toEqual(
      local.map((client) =>
        client.snippet.replace(ENDPOINT, "https://mcp.example.com/mcp"),
      ),
    );
  });
});
