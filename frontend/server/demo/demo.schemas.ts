/**
 * Shapes the playground hands to the interface.
 *
 * The backend owns these, so this mirrors `app/demo/schemas.py` rather than
 * deriving anything from it. Kept in one place so the components agree on what a
 * run looks like.
 */

export type DemoToolCall = {
  name: string;
  /** Where the tool lives: the agent's own code, or the MCP server. */
  source: "agent" | "mcp";
  arguments: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error: string | null;
  /** Set while the run waits on a person: the agent asked and has not been answered. */
  pending: boolean;
};

export type DemoRun = {
  calls: DemoToolCall[];
  /** Set when the MCP door refused the call, which is the anonymous case. */
  refused: string | null;
  /** Set when a tool failed for a reason that is not the door. */
  failed: string | null;
  /** Set when the run stopped to ask the visitor something. */
  approval: string | null;
  /** What comes back with the decision to carry the same run on. */
  thread_id: string | null;
};

export type DemoRunRequest = {
  thread_id?: string;
  decision?: "accept" | "reject";
};
