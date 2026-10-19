/**
 * What the backend's `/v1` read endpoints return.
 *
 * Hand-written rather than generated: there are seven of them, they change when
 * a service changes, and a stale field surfaces in the page that renders it.
 */

export type Kind = "component" | "image";

/**
 * Where an artifact ended up, not a grade.
 *
 * ``candidate`` is what a run is while nobody has turned it down; ``rejected``
 * is a run the sandbox would not build or the judge scored below its bar, and it
 * is kept either way. A task makes one artifact, so this is the artifact's fate
 * rather than one step of a history.
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
  /** The maker's public name; null when nobody claimed it. */
  author: string | null;
  /** The render the block was published from, when the run left one. */
  screenshot_path: string | null;
}

export interface Component extends ComponentSummary {
  /**
   * The project: path → file, as the harness left it. Always at least one file —
   * a block is a project even when it is one file, so the item view has a single
   * shape to render.
   */
  files: Record<string, string>;
  /**
   * Which of those files the block is: the one the scaffold imports, and the one
   * a reader opens first. A path, not a copy of the file.
   */
  entry: string;
  /**
   * What it imports from packages, with the version it was built against. Read
   * out of the project by the sandbox rather than declared by whoever wrote it,
   * so it is what a visitor has to install and not a claim.
   */
  dependencies: Record<string, string> | null;
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

/**
 * The artifact one task produced: its project, what the judge said, where it went.
 *
 * One per task — the API still calls it a generation and still returns a list,
 * because that is the published shape — so a view reads the one there is rather
 * than walking a history.
 */
export interface Generation {
  id: string;
  task_id: string | null;
  component_id: string | null;
  attempt_no: number;
  /** The project, as the run left it: at least the entry file. */
  files: Record<string, string>;
  /** Which of those files the block is. A path, not a copy of the file. */
  entry: string;
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
  /** The maker's public name; null for the house. */
  author: string | null;
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
  /**
   * True when the brief had already been built: the task never ran, and it points
   * straight at the block that answered it.
   */
  cached: boolean;
  steps: TaskStep[];
}

/** A task with the artifact it produced; the list keeps tasks lean, the detail carries it. */
export interface TaskDetail extends Task {
  generations: Generation[];
}

/**
 * Something the agent found while working, shown as a card in the conversation.
 *
 * A block or a picture the registry already has: `path` is the Cloudinary public
 * id of what to show, and it is null when there is nothing (a seeded block has no
 * render), in which case the card falls back to its words.
 */
export interface Suggestion {
  kind: "component" | "image";
  id: string;
  title: string;
  detail: string;
  path: string | null;
  width: number | null;
  height: number | null;
}
