import { headers } from "next/headers";

import { env } from "@/lib/env";

/**
 * The origin every auth redirect and email link is built from.
 *
 * In production this is a configured value, never the request's Host header:
 * those headers are attacker-controlled in enough proxy setups that using them
 * would let somebody route a confirmation or reset link to their own domain.
 * Development keeps the request origin so a laptop or a LAN address still works
 * without a second environment file.
 */
export async function siteUrl(): Promise<string> {
  const configured = env.SITE_URL?.replace(/\/+$/, "");
  if (configured) {
    return configured;
  }

  if (env.NODE_ENV !== "production") {
    const incoming = await headers();
    const host =
      incoming.get("x-forwarded-host") ??
      incoming.get("host") ??
      "localhost:3000";
    const protocol = incoming.get("x-forwarded-proto") ?? "http";

    return `${protocol}://${host}`;
  }

  // Fail closed rather than fall back to a request header. A missing setting is
  // a deployment mistake that should be noticed before an auth link goes out.
  throw new Error("SITE_URL must be set in production.");
}
