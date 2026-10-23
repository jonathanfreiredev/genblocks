import "@/lib/zod-config";

import { z } from "zod";

export const reportSchema = z.object({
  targetKind: z.enum(["component", "image"]),
  targetId: z.string().uuid(),
  reason: z.enum([
    "sexual",
    "minor",
    "violence",
    "hate",
    "harassment",
    "self_harm",
    "illegal",
    "malware",
    "privacy",
    "real_person",
    "brand",
    "other",
  ]),
  details: z.string().trim().max(2000).optional(),
});

export const resolveReportSchema = z.object({
  reportId: z.string().uuid(),
  status: z.enum(["reviewing", "resolved", "dismissed"]),
  resolution: z.string().trim().max(2000).optional(),
  takeDown: z.boolean().default(false),
});
