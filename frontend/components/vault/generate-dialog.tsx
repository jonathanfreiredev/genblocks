"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldLabel } from "@/components/ui/field";
import { Textarea } from "@/components/ui/textarea";

/**
 * The steps a brief goes through once a worker picks it up. The same names the
 * task checklist prints, so the dialog's promise and the task's record agree.
 */
const STEPS = [
  "Moderating the brief",
  "Retrieving references",
  "Generating the block",
  "Judging the attempt",
  "Publishing the block",
];

/**
 * The vault's one action.
 *
 * The dialog is real and the brief field works; what is missing is the worker on
 * the other end, and the footer says so instead of pretending a click did
 * something. The checklist is shown now because it is the shape of the task the
 * brief will become, not a decoration.
 */
export function GenerateDialog() {
  return (
    <Dialog>
      <DialogTrigger render={<Button className="w-full" />}>
        Generate with AI
      </DialogTrigger>

      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="type-title">Generate a block</DialogTitle>
          <DialogDescription>
            One brief becomes one task. The task runs in the background and its
            checklist stays at your tasks while it works.
          </DialogDescription>
        </DialogHeader>

        <Field>
          <FieldLabel htmlFor="brief" className="type-label text-ink-faint">
            Brief
          </FieldLabel>
          <Textarea
            id="brief"
            name="brief"
            rows={4}
            placeholder="A pricing page for a developer tool: three tiers, an annual toggle, one comparison row per feature."
          />
        </Field>

        <ol className="type-meta text-ink-faint flex flex-col gap-1.5">
          {STEPS.map((step, index) => (
            <li key={step} className="flex gap-3">
              <span className="tabular-nums">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span>{step}</span>
            </li>
          ))}
        </ol>

        <DialogFooter className="sm:justify-between">
          <p className="type-meta text-ink-faint">
            Not wired yet. Nothing leaves this box.
          </p>
          <Button type="button" disabled>
            Generate
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
