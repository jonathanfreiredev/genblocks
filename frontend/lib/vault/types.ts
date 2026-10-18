/**
 * What the backend's `/v1` read endpoints return.
 *
 * Hand-written rather than generated: there are seven of them, they change when
 * a service changes, and a stale field surfaces in the page that renders it.
 */

export type Kind = "component" | "image";

/**
 * An attempt's verdict: where the artifact ended up, not a grade.
 *
 * ``candidate`` is an attempt nobody has judged yet; the judge either publishes
 * it or rejects it, and a rejected attempt is kept.
 */
export type Verdict = "candidate" | "published" | "rejected";

export type StepStatus = "pending" | "running" | "succeeded" | "failed";

export type TaskStatus =
  "pending" | "running" | "succeeded" | "failed" | "interrupted";

export interface OffsetPage<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

/** A node of the two-level taxonomy: level 1 is a kind, level 2 a type. */
export interface Category {
  id: string;
  parent_id: string | null;
  kind: Kind;
  slug: string;
  name: string;
  level: number;
}

/** What a gallery cell needs: no code, no spec, just enough to browse. */
export interface ComponentSummary {
  id: string;
  slug: string;
  title: string;
  description: string;
  category_id: string;
  created_at: string;
}

export interface Component extends ComponentSummary {
  code: string;
  delivery_prompt: string;
  spec: Record<string, unknown> | null;
  winning_generation_id: string | null;
  created_by: string | null;
  license: string;
}

/**
 * What the sandbox found on one attempt.
 *
 * `blocked` is the field the pipeline acted on: a fatal check failed, and the
 * attempt was not published. Everything else is evidence, kept as it was
 * reported — axe's own ids and impacts rather than a count of them.
 */
export interface HarnessCheck {
  name: string;
  ok: boolean;
  detail: string | null;
}

export interface HarnessViolation {
  id: string;
  impact: string | null;
  help: string;
  nodes: number;
}

export interface HarnessChecks {
  blocked: boolean;
  passed: number;
  total: number;
  checks: HarnessCheck[];
  violations: HarnessViolation[];
}

/** One attempt: the code it produced, what the judge said, and where it went. */
export interface Generation {
  id: string;
  task_id: string | null;
  component_id: string | null;
  attempt_no: number;
  code: string;
  screenshot_path: string | null;
  checks: HarnessChecks | null;
  scores: Record<string, number> | null;
  verdict: Verdict;
  rubric_version: string | null;
  model: string | null;
  langfuse_trace_id: string | null;
  created_at: string;
}

/**
 * A stock image and its own judge panel.
 *
 * `path` is a Cloudinary public id, not a URL: the delivery host and the
 * transform belong to whoever renders it. An image carries its scores directly,
 * because unlike a block it is not produced by a task.
 */
export interface Image {
  id: string;
  prompt: string;
  path: string;
  width: number;
  height: number;
  category_id: string;
  created_by: string | null;
  license: string;
  model: string | null;
  scores: Record<string, number> | null;
  rubric_version: string | null;
  langfuse_trace_id: string | null;
  created_at: string;
}

export interface TaskStep {
  id: string;
  index: number;
  name: string;
  status: StepStatus;
  detail: Record<string, unknown> | null;
  started_at: string | null;
  finished_at: string | null;
}

export interface Task {
  id: string;
  kind: string;
  status: TaskStatus;
  brief: string;
  component_id: string | null;
  created_at: string;
  finished_at: string | null;
  error: string | null;
  langfuse_trace_id: string | null;
  steps: TaskStep[];
}

/** A task with its attempts; the list keeps tasks lean, the detail carries them. */
export interface TaskDetail extends Task {
  generations: Generation[];
}
