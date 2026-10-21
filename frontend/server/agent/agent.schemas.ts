import { z } from "zod";

/**
 * What the browser may say to the conversation endpoint, restated from the
 * backend (`app/agent/schemas.py`).
 *
 * The backend is still the one that checks: this is here so a message the agent
 * could not have sent is refused before it becomes a round trip. A brief has its
 * own bounds in the backend; the composer sends messages, not briefs, because
 * writing the brief is the agent's job.
 */
export const MESSAGE_MAX_LENGTH = 4000;
export const THREAD_MIN_LENGTH = 8;
export const THREAD_MAX_LENGTH = 100;

export const chatRequestSchema = z.object({
  message: z
    .string()
    .trim()
    .min(1, "Say something first.")
    .max(
      MESSAGE_MAX_LENGTH,
      `A message can be at most ${MESSAGE_MAX_LENGTH} characters.`,
    ),
  threadId: z
    .string()
    .trim()
    .min(THREAD_MIN_LENGTH, "A conversation needs a name.")
    .max(THREAD_MAX_LENGTH, "That conversation name is too long."),
});

export type ChatRequest = z.infer<typeof chatRequestSchema>;

/**
 * What the confirmation button sends. It mirrors the backend's `ConfirmRequest`:
 * a component has just a brief, an image also carries its size and category.
 */
export const confirmProposalSchema = z.object({
  kind: z.enum(["component", "image"]).default("component"),
  brief: z.string().trim().min(1).max(2_000),
  force: z.boolean().default(false),
  width: z.number().int().min(256).max(1_536).nullable().optional(),
  height: z.number().int().min(256).max(1_536).nullable().optional(),
  category: z.string().trim().min(1).max(80).nullable().optional(),
});

export type ConfirmProposal = z.infer<typeof confirmProposalSchema>;
