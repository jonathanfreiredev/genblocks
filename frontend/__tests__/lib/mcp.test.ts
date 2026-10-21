import { describe, expect, test } from "vitest";

import {
  configuredMcpEndpoint,
  hostnameOf,
  isLocalHost,
  localMcpEndpoint,
  resolveMcpEndpoint,
} from "@/lib/mcp";

describe("hostnameOf", () => {
  test("drops the port the browser connects to", () => {
    expect(hostnameOf("localhost:3000")).toBe("localhost");
    expect(hostnameOf("genblocks.jonathanfreire.com")).toBe(
      "genblocks.jonathanfreire.com",
    );
  });

  test("keeps an IPv6 address in the form a URL can use", () => {
    expect(hostnameOf("[::1]:3000")).toBe("[::1]");
  });

  test("has no answer for a header that is not a host", () => {
    expect(hostnameOf("")).toBeNull();
    expect(hostnameOf(null)).toBeNull();
  });
});

describe("isLocalHost", () => {
  test("recognises a development machine and its network", () => {
    for (const host of [
      "localhost:3000",
      "127.0.0.1:3000",
      "[::1]:3000",
      "0.0.0.0:3000",
      "192.168.1.20:3000",
      "10.0.0.4:3000",
      "172.20.1.5:3000",
      "studio.local:3000",
      "host.docker.internal:3000",
    ]) {
      expect(isLocalHost(host), host).toBe(true);
    }
  });

  test("does not mistake a deployment for one", () => {
    for (const host of [
      "genblocks.jonathanfreire.com",
      "8.8.8.8",
      "172.32.0.1",
      "192.169.0.1",
    ]) {
      expect(isLocalHost(host), host).toBe(false);
    }
  });
});

describe("localMcpEndpoint", () => {
  test("uses the address the reader opened, not a fixed localhost", () => {
    expect(localMcpEndpoint("192.168.1.20:3000")).toBe(
      "http://192.168.1.20:8001/mcp",
    );
    expect(localMcpEndpoint("localhost:3000")).toBe(
      "http://localhost:8001/mcp",
    );
  });

  test("falls back to localhost when there is no host", () => {
    expect(localMcpEndpoint(null)).toBe("http://localhost:8001/mcp");
  });
});

describe("configuredMcpEndpoint", () => {
  test("accepts the base URL or the full endpoint", () => {
    expect(configuredMcpEndpoint("https://mcp.example.com")).toBe(
      "https://mcp.example.com/mcp",
    );
    expect(configuredMcpEndpoint("https://mcp.example.com/mcp/")).toBe(
      "https://mcp.example.com/mcp",
    );
  });

  test("says nothing rather than inventing an address", () => {
    expect(configuredMcpEndpoint("")).toBeNull();
    expect(configuredMcpEndpoint(undefined)).toBeNull();
  });
});

describe("resolveMcpEndpoint", () => {
  test("a local request ignores the production value", () => {
    expect(
      resolveMcpEndpoint("localhost:3000", "https://mcp.example.com"),
    ).toEqual({ mode: "local", endpoint: "http://localhost:8001/mcp" });
  });

  test("a deployment uses the value it published", () => {
    expect(
      resolveMcpEndpoint(
        "genblocks.jonathanfreire.com",
        "https://mcp.example.com",
      ),
    ).toEqual({ mode: "production", endpoint: "https://mcp.example.com/mcp" });
  });

  test("a deployment without one has no endpoint to show", () => {
    expect(
      resolveMcpEndpoint("genblocks.jonathanfreire.com", undefined),
    ).toEqual({
      mode: "production",
      endpoint: null,
    });
  });
});
