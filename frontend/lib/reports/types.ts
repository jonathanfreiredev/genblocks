export type ReportTarget = "component" | "image";

export type ReportReason =
  | "sexual"
  | "minor"
  | "violence"
  | "hate"
  | "harassment"
  | "self_harm"
  | "illegal"
  | "malware"
  | "privacy"
  | "real_person"
  | "brand"
  | "other";

export type ReportStatus = "open" | "reviewing" | "resolved" | "dismissed";

export interface Report {
  id: string;
  target_kind: ReportTarget;
  target_id: string;
  target_slug: string | null;
  target_title: string | null;
  reason: ReportReason;
  details: string | null;
  status: ReportStatus;
  resolution: string | null;
  reporter: string | null;
  created_at: string;
  resolved_at: string | null;
}

export const REPORT_REASONS: { value: ReportReason; label: string }[] = [
  { value: "sexual", label: "Sexual content" },
  { value: "minor", label: "Involves a minor" },
  { value: "violence", label: "Violence or gore" },
  { value: "hate", label: "Hate or extremism" },
  { value: "harassment", label: "Harassment" },
  { value: "self_harm", label: "Self-harm" },
  { value: "illegal", label: "Illegal activity" },
  { value: "malware", label: "Malware or phishing" },
  { value: "privacy", label: "Personal data" },
  { value: "real_person", label: "A real person" },
  { value: "brand", label: "A brand or trademark" },
  { value: "other", label: "Something else" },
];

export const REPORT_STATUS_LABELS: Record<ReportStatus, string> = {
  open: "Open",
  reviewing: "Reviewing",
  resolved: "Resolved",
  dismissed: "Dismissed",
};
