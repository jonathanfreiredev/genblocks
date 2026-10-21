"use server";

import { revalidatePath } from "next/cache";
import { returnServerError } from "next-safe-action";
import { z } from "zod";

import { backendErrorMessage } from "@/lib/api-error";
import { protectedProcedure } from "@/lib/safe-action";
import { deleteAdminItem } from "@/lib/admin/api";

const itemSchema = z.object({
  kind: z.enum(["component", "image"]),
  id: z.string().uuid(),
});

export const deleteItemAction = protectedProcedure
  .inputSchema(itemSchema)
  .action(async ({ parsedInput, ctx }) => {
    if (!ctx.user.isAdmin) {
      returnServerError({ code: 403, message: "Only an operator may delete items." });
    }

    try {
      await deleteAdminItem(ctx.session.token, parsedInput.kind, parsedInput.id);
      revalidatePath("/admin/items");
      revalidatePath("/blocks");
    } catch (error) {
      returnServerError({
        code: 403,
        message: backendErrorMessage(
          error instanceof Error ? error.message : undefined,
          "The item could not be deleted.",
        ),
      });
    }

    return { success: true };
  });
