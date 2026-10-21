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
import { toast } from "@/components/ui/toast";
import type { AdminItem } from "@/lib/admin/types";
import { deleteItemAction } from "@/server/admin/items.actions";

export function AdminItemActions({ item }: { item: AdminItem }) {
  const router = useRouter();
  const [confirming, setConfirming] = useState(false);
  const [pending, startTransition] = useTransition();

  function remove() {
    startTransition(async () => {
      const result = await deleteItemAction({ kind: item.kind, id: item.id });
      if (result.serverError) {
        toast.add({
          title: "Could not delete",
          description:
            result.serverError.message || "Try again in a moment.",
          type: "error",
        });
        return;
      }
      toast.add({
        title: "Item deleted",
        description: "The row and its Cloudinary asset are gone.",
        type: "success",
      });
      setConfirming(false);
      router.refresh();
    });
  }

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="destructive"
        size="sm"
        disabled={pending}
        onClick={() => setConfirming(true)}
      >
        Delete
      </Button>

      <Dialog open={confirming} onOpenChange={setConfirming}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Permanently delete this item?</DialogTitle>
            <DialogDescription>
              This removes the database row and the Cloudinary asset. It cannot
              be undone.
              {item.kind === "image"
                ? " Blocks that use this image will keep a broken reference."
                : " Its screenshot and generation history are removed too."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setConfirming(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={pending} onClick={remove}>
              {pending ? "Deleting…" : "Delete forever"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
