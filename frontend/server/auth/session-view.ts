import type { Session } from "./auth.lib";

/**
 * What the client-side chrome is allowed to know about the session.
 *
 * A Supabase access token is a bearer credential. It must never cross the
 * server/client boundary, even though it lives in an httpOnly cookie on the way
 * in: a client component's props are serialised into the RSC payload, and a
 * TypeScript annotation does not remove fields at runtime.
 *
 * Keep this shape as the only session data a Client Component receives.
 */
export type SessionView = {
  user: {
    name: string;
  };
};

export function sessionView(session: Session | null): SessionView | null {
  if (session === null) {
    return null;
  }

  return { user: { name: session.user.name } };
}
