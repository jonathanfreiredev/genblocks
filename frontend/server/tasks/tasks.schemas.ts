import { z } from "zod";

/**
 * The brief's bounds, restated from the backend (`app/tasks/schemas.py`).
 *
 * The backend is still the one that checks: a brief that arrives over HTTP is
 * validated there, and a tool call is validated there. These numbers exist so
 * the dialog can refuse a brief before it becomes a round trip, and they are
 * written once so the dialog, the action and the form cannot drift apart.
 */
export const BRIEF_MIN_LENGTH = 10;
export const BRIEF_MAX_LENGTH = 2000;

export const createTaskSchema = z.object({
  brief: z
    .string()
    .trim()
    .min(
      BRIEF_MIN_LENGTH,
      `A brief needs at least ${BRIEF_MIN_LENGTH} characters.`,
    )
    .max(
      BRIEF_MAX_LENGTH,
      `A brief can be at most ${BRIEF_MAX_LENGTH} characters.`,
    ),
});
