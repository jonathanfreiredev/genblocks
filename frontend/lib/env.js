import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

export const env = createEnv({
  /**
   * Specify your server-side environment variables schema here. This way you can ensure the app
   * isn't built with invalid env vars.
   */
  server: {
    NODE_ENV: z
      .enum(["development", "production", "test"])
      .default("development"),
    BACKEND_URL: z.string(),
    // Supabase secret key (sb_secret_..., replaces the legacy service_role key).
    // Used by the admin client to delete a user. Server-only: it bypasses RLS
    // and must never reach the browser.
    SUPABASE_SECRET_KEY: z.string().min(1),
    // Public address of the MCP server, as clients reach it in production. The
    // connect page shows this when the app is not served from localhost; locally
    // it derives the endpoint from the request instead. Optional so a local
    // checkout runs without it. Accepts the base URL or the full `/mcp` URL.
    MCP_URL: z.string().url().optional(),
    // Canonical origin of this app, used to build the links Supabase emails and
    // to redirect after authentication. In production it must be set: deriving
    // these from the request Host header would let an attacker choose where a
    // confirmation or password-reset link lands. In development the request
    // origin is a safe fallback.
    SITE_URL: z.string().url().optional(),
  },

  /**
   * Specify your client-side environment variables schema here. This way you can ensure the app
   * isn't built with invalid env vars. To expose them to the client, prefix them with
   * `NEXT_PUBLIC_`.
   */
  client: {
    NEXT_PUBLIC_SUPABASE_URL: z.string().url(),
    // Supabase publishable key (sb_publishable_..., replaces the legacy anon key).
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: z.string().min(1),
    // Comma-separated list of enabled login methods: "email", "google".
    NEXT_PUBLIC_AUTH_PROVIDERS: z.string().default("email"),
    // Cloudinary cloud name the block renders and stock images are delivered
    // from. Optional: the backend uploads there, and without it a view falls back
    // to the recipe its row was generated from instead of pretending to show a
    // picture.
    NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME: z.string().optional(),
  },

  /**
   * You can't destruct `process.env` as a regular object in the Next.js edge runtimes (e.g.
   * middlewares) or client-side so we need to destruct manually.
   */
  runtimeEnv: {
    NODE_ENV: process.env.NODE_ENV,
    BACKEND_URL: process.env.BACKEND_URL,
    SUPABASE_SECRET_KEY: process.env.SUPABASE_SECRET_KEY,
    MCP_URL: process.env.MCP_URL,
    SITE_URL: process.env.SITE_URL,
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY,
    NEXT_PUBLIC_AUTH_PROVIDERS: process.env.NEXT_PUBLIC_AUTH_PROVIDERS,
    NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME:
      process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME,
  },
  /**
   * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially
   * useful for Docker builds.
   */
  skipValidation: !!process.env.SKIP_ENV_VALIDATION,
  /**
   * Makes it so that empty strings are treated as undefined. `SOME_VAR: z.string()` and
   * `SOME_VAR=''` will throw an error.
   */
  emptyStringAsUndefined: true,
});
