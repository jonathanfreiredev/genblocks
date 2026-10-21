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
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "@/components/ui/toast";
import type { AdminUser } from "@/lib/admin/types";
import { banUserAction, unbanUserAction } from "@/server/admin/users.actions";

export function AdminUserActions({ user }: { user: AdminUser }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const [pending, startTransition] = useTransition();

  function showWarning(warning: string | null | undefined) {
    if (warning) {
      toast.add({ title: "Partly done", description: warning, type: "error" });
    }
  }

  function ban() {
    startTransition(async () => {
      const result = await banUserAction({
        userId: user.id,
        reason: reason || undefined,
      });
      if (result.serverError) {
        toast.add({
          title: "Could not ban",
          description: result.serverError.message || "Try again.",
          type: "error",
        });
        return;
      }
      showWarning(result.data?.warning);
      toast.add({
        title: "User banned",
        description: "They can only browse as an anonymous visitor.",
        type: "success",
      });
      setOpen(false);
      setReason("");
      router.refresh();
    });
  }

  function unban() {
    startTransition(async () => {
      const result = await unbanUserAction({ userId: user.id });
      if (result.serverError) {
        toast.add({
          title: "Could not unban",
          description: result.serverError.message || "Try again.",
          type: "error",
        });
        return;
      }
      showWarning(result.data?.warning);
      toast.add({
        title: "User unbanned",
        description: "They can sign in again.",
        type: "success",
      });
      router.refresh();
    });
  }

  if (user.banned_at) {
    return (
      <Button variant="outline" size="sm" disabled={pending} onClick={unban}>
        {pending ? "Unbanning…" : "Unban"}
      </Button>
    );
  }

  return (
    <>
      <Button
        variant="destructive"
        size="sm"
        disabled={pending}
        onClick={() => setOpen(true)}
      >
        Ban
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ban this user?</DialogTitle>
            <DialogDescription>
              Their existing token stops working and Supabase refuses a new
              login. They can still browse as an anonymous visitor. Their
              published blocks are not deleted.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-2">
            <Label htmlFor={`ban-reason-${user.id}`}>Reason (optional)</Label>
            <Textarea
              id={`ban-reason-${user.id}`}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              placeholder="What happened?"
              maxLength={500}
            />
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={pending} onClick={ban}>
              {pending ? "Banning…" : "Ban user"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
