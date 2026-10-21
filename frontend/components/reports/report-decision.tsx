"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";
import { resolveReportAction } from "@/server/reports/reports.actions";

/**
 * The operator's half of the queue.
 *
 * The note is required in practice, not by the input: a takedown without a
 * sentence is the one decision nobody can review later. The actions are
 * separate so dismissing is not a disabled state of taking down.
 */
export function ReportDecision({ reportId }: { reportId: string }) {
  const router = useRouter();
  const [resolution, setResolution] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [pending, startTransition] = useTransition();

  function decide(
    status: "reviewing" | "resolved" | "dismissed",
    takeDown: boolean,
  ) {
    startTransition(async () => {
      const result = await resolveReportAction({
        reportId,
        status,
        resolution: resolution.trim() || undefined,
        takeDown,
      });

      if (result.serverError) {
        toast.add({
          title: "The decision was not saved",
          description: result.serverError.message || "Try again in a moment.",
          type: "error",
        });
        return;
      }

      toast.add({
        title: takeDown
          ? "Item taken down"
          : status === "reviewing"
            ? "Report marked reviewing"
            : "Report dismissed",
        description: takeDown
          ? "The item and its Cloudinary asset are gone. The report keeps a snapshot for the record."
          : status === "reviewing"
            ? "The queue now shows that somebody is looking at it."
            : "The item stays public.",
        type: "success",
      });
      setResolution("");
      router.refresh();
    });
  }

  return (
    <div className="flex flex-col gap-3">
      <Textarea
        value={resolution}
        onChange={(event) => setResolution(event.target.value)}
        maxLength={2000}
        placeholder="Why this decision? The next reviewer will read this."
        aria-label="Resolution note"
      />
      <div className="flex flex-wrap gap-2">
        <Button
          variant="secondary"
          size="sm"
          disabled={pending}
          onClick={() => decide("reviewing", false)}
        >
          Start review
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={pending}
          onClick={() => decide("dismissed", false)}
        >
          Dismiss
        </Button>
        <Button
          variant="destructive"
          size="sm"
          disabled={pending}
          onClick={() => setConfirming(true)}
        >
          Take down
        </Button>
      </div>

      <Dialog open={confirming} onOpenChange={setConfirming}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Take this item down?</DialogTitle>
            <DialogDescription>
              The item, its page and its Cloudinary asset will be permanently
              removed. The report, the note and a snapshot of the item stay for
              the record. This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={pending}
              onClick={() => {
                setConfirming(false);
                decide("resolved", true);
              }}
            >
              {pending ? "Saving…" : "Confirm takedown"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
