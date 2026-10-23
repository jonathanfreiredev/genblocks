import { z } from "zod";

/**
 * Zod normally compiles a fast validator with `Function("")` on first use. The
 * production CSP forbids eval, so the browser logs a violation even though Zod
 * catches the failure and falls back. Turning JIT off keeps the console and the
 * DevTools Issues panel clean without weakening the policy.
 */
z.config({ jitless: true });
