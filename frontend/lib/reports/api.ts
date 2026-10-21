import "server-only";

import { env } from "@/lib/env";
import type { OffsetPage } from "@/lib/vault/types";
import type { Report, ReportReason, ReportStatus, ReportTarget } from "./types";

export class ReportsUnreadable extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ReportsUnreadable";
  }
}

async function call<T>(
  path: string,
  token: string,
  init?: RequestInit,
): Promise<T> {
  const url = new URL(`/v1${path}`, env.BACKEND_URL);
  const response = await fetch(url, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ReportsUnreadable(
      typeof body.detail === "string"
        ? body.detail
        : `The reports API answered ${response.status}.`,
    );
  }

  return (await response.json()) as T;
}

export function createReport(
  token: string,
  input: {
    target_kind: ReportTarget;
    target_id: string;
    reason: ReportReason;
    details?: string;
  },
): Promise<Report> {
  return call<Report>("/reports", token, {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listReports(
  token: string,
  query: { status?: ReportStatus; limit?: number; offset?: number } = {},
): Promise<OffsetPage<Report>> {
  const params = new URLSearchParams();
  if (query.status) params.set("status", query.status);
  if (query.limit) params.set("limit", String(query.limit));
  if (query.offset) params.set("offset", String(query.offset));
  const suffix = params.size ? `?${params}` : "";

  return call<OffsetPage<Report>>(`/admin/reports${suffix}`, token);
}

export function resolveReport(
  token: string,
  reportId: string,
  input: { status: ReportStatus; resolution?: string; take_down: boolean },
): Promise<Report> {
  return call<Report>(`/admin/reports/${reportId}`, token, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}
