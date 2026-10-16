import type { CookieOptions } from "@supabase/ssr";

/**
 * Cookie options shared by every Supabase server client.
 *
 * `httpOnly` is safe here because this project has no browser Supabase client:
 * the session is only ever read and refreshed on the server (proxy + server
 * actions), never from JavaScript. `secure` is enabled in production so the
 * session cookies are never sent over plain HTTP.
 */
export const cookieOptions: CookieOptions = {
  path: "/",
  sameSite: "lax",
  httpOnly: true,
  secure: process.env.NODE_ENV === "production",
};
