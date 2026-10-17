"use server";

import { returnServerError } from "next-safe-action";

import { backendErrorMessage } from "@/lib/api-error";
import { env } from "@/lib/env";
import { protectedProcedure } from "@/lib/safe-action";
import type { Task } from "@/lib/vault/types";
import { createTaskSchema } from "./tasks.schemas";

/**
 * Hand a brief to the generator.
 *
 * The session's own token goes with the request, so the task belongs to the
 * caller before it exists: the API reads the owner from the credential and never
 * from the body. 202 comes back with the queued task — the row the caller now
 * follows — rather than a block, because there is no block yet.
 */
export const createTaskAction = protectedProcedure
  .inputSchema(createTaskSchema)
  .action(async ({ parsedInput, ctx }) => {
    const response = await fetch(`${env.BACKEND_URL}/v1/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${ctx.session.token}`,
      },
      body: JSON.stringify({ brief: parsedInput.brief }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));

      returnServerError({
        code: response.status,
        message: backendErrorMessage(
          errorData.detail,
          "The generator did not accept the brief.",
        ),
      });
    }

    return { task: (await response.json()) as Task };
  });
