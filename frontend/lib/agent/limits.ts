/**
 * Bounds shared by the browser composer and the server schema.
 *
 * This file deliberately has no imports: `agent-chat.tsx` is a client
 * component, and importing the Zod schema just to read one number pulled the
 * whole validator into the catalogue bundle.
 */
export const MESSAGE_MAX_LENGTH = 4000;
export const THREAD_MIN_LENGTH = 8;
export const THREAD_MAX_LENGTH = 100;
