import { describe, expect, test, vi } from "vitest";

type AuthProvidersModule = typeof import("@/lib/auth-providers");

/**
 * The module reads the env var at import time, so each case stubs the value and
 * re-imports a fresh copy.
 */
async function loadAuthProviders(
  value: string | undefined,
): Promise<AuthProvidersModule> {
  vi.stubEnv("NEXT_PUBLIC_AUTH_PROVIDERS", value);
  vi.resetModules();

  return import("@/lib/auth-providers");
}

describe("authProviders", () => {
  test("defaults to email when the variable is unset", async () => {
    const { authProviders } = await loadAuthProviders(undefined);

    expect(authProviders).toEqual(["email"]);
  });

  test("parses a comma-separated list", async () => {
    const { authProviders } = await loadAuthProviders("email,google");

    expect(authProviders).toEqual(["email", "google"]);
  });

  test("supports a single provider", async () => {
    const { authProviders } = await loadAuthProviders("google");

    expect(authProviders).toEqual(["google"]);
  });

  test("ignores unknown providers", async () => {
    const { authProviders } = await loadAuthProviders("google,facebook");

    expect(authProviders).toEqual(["google"]);
  });

  test("normalises whitespace and casing", async () => {
    const { authProviders } = await loadAuthProviders(" Email , GOOGLE ");

    expect(authProviders).toEqual(["email", "google"]);
  });

  test("falls back to email when nothing valid remains", async () => {
    const { authProviders } = await loadAuthProviders("");

    expect(authProviders).toEqual(["email"]);
  });

  test("isProviderEnabled reflects the parsed list", async () => {
    const { isProviderEnabled } = await loadAuthProviders("google");

    expect(isProviderEnabled("google")).toBe(true);
    expect(isProviderEnabled("email")).toBe(false);
  });
});
