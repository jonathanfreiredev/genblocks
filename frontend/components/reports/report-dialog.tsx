"use client";

import { FlagIcon } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useTransition } from "react";

import { Button, buttonVariants } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
} from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";
import {
  REPORT_REASONS,
  type ReportReason,
} from "@/lib/reports/types";
import { reportContentAction } from "@/server/reports/reports.actions";

/**
 * The visitor's half of the report queue.
 *
 * A report is not a takedown: it puts the artifact in front of an operator, who
 * sees the same page and decides. The dialog says that plainly so nobody expects
 * the picture to disappear the moment they press send.
 */
export function ReportDialog({
  targetKind,
  targetId,
  signedIn,
}: {
  targetKind: "component" | "image";
  targetId: string;
  signedIn: boolean;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<ReportReason>("other");
  const [details, setDetails] = useState("");
  const [pending, startTransition] = useTransition();

  if (!signedIn) {
    return (
      <Link
        href={`/auth/login?next=${encodeURIComponent(pathname)}`}
        aria-label="Sign in to report this item"
        className={buttonVariants({ variant: "ghost", size: "sm" })}
      >
        <FlagIcon data-icon="inline-start" />
        Sign in to report
      </Link>
    );
  }

  function submit() {
    startTransition(async () => {
      const result = await reportContentAction({
        targetKind,
        targetId,
        reason,
        details: details.trim() || undefined,
      });

      if (result.serverError) {
        toast.add({
          title: "The report was not sent",
          description: result.serverError.message || "Try again in a moment.",
          type: "error",
        });
        return;
      }

      toast.add({
        title: "Report sent",
        description:
          "An operator will review it. Nothing is removed automatically.",
        type: "success",
      });
      setOpen(false);
      setDetails("");
      setReason("other");
    });
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger
        render={<Button variant="ghost" size="sm" />}
        aria-label="Report this item"
      >
        <FlagIcon data-icon="inline-start" />
        Report
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Report this item</DialogTitle>
          <DialogDescription>
            A person reviews every report. Removing the item is their decision,
            not an automatic consequence of sending this.
          </DialogDescription>
        </DialogHeader>

        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="report-reason">
              What is wrong with it?
            </FieldLabel>
            <Select
              value={reason}
              onValueChange={(value) => setReason(value as ReportReason)}
            >
              <SelectTrigger id="report-reason" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {REPORT_REASONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </Field>

          <Field>
            <FieldLabel htmlFor="report-details">Anything else?</FieldLabel>
            <Textarea
              id="report-details"
              value={details}
              onChange={(event) => setDetails(event.target.value)}
              maxLength={2000}
              placeholder="A sentence or two helps the operator find the problem."
            />
            <FieldDescription>
              Do not include personal data. {details.length}/2000
            </FieldDescription>
          </Field>
        </FieldGroup>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={pending}>
            {pending ? "Sending…" : "Send report"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
