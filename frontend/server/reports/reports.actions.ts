"use server";

import { revalidatePath } from "next/cache";
import { returnServerError } from "next-safe-action";

import { backendErrorMessage } from "@/lib/api-error";
import { protectedProcedure } from "@/lib/safe-action";
import { createReport, resolveReport } from "@/lib/reports/api";
import { reportSchema, resolveReportSchema } from "./reports.schemas";

export const reportContentAction = protectedProcedure
  .inputSchema(reportSchema)
  .action(async ({ parsedInput, ctx }) => {
    try {
      await createReport(ctx.session.token, {
        target_kind: parsedInput.targetKind,
        target_id: parsedInput.targetId,
        reason: parsedInput.reason,
        details: parsedInput.details || undefined,
      });
    } catch (error) {
      returnServerError({
        code: 400,
        message: backendErrorMessage(
          error instanceof Error ? error.message : undefined,
          "The report could not be sent.",
        ),
      });
    }

    return { success: true };
  });

export const resolveReportAction = protectedProcedure
  .inputSchema(resolveReportSchema)
  .action(async ({ parsedInput, ctx }) => {
    try {
      const report = await resolveReport(
        ctx.session.token,
        parsedInput.reportId,
        {
          status: parsedInput.status,
          resolution: parsedInput.resolution || undefined,
          take_down: parsedInput.takeDown,
        },
      );

      revalidatePath("/admin/reports");
      revalidatePath("/blocks");
      revalidatePath("/images");
      if (report.target_kind === "component" && report.target_slug) {
        revalidatePath(`/blocks/${report.target_slug}`);
      }
      if (report.target_kind === "image" && report.target_slug) {
        revalidatePath(`/images/${report.target_slug}`);
      }
    } catch (error) {
      returnServerError({
        code: 403,
        message: backendErrorMessage(
          error instanceof Error ? error.message : undefined,
          "The report could not be resolved.",
        ),
      });
    }

    return { success: true };
  });
