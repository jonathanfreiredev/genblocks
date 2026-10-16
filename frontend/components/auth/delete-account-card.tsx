"use client";

import { useState } from "react";

import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../ui/dialog";
import { DeleteAccountForm } from "./delete-account-form";

/**
 * Destructive actions live in their own card, visually separated and red, so
 * they are never mistaken for a routine edit.
 */
export const DeleteAccountCard = () => {
  const [isOpen, setOpen] = useState(false);

  return (
    <Card className="bg-destructive/5 ring-destructive/40">
      <CardHeader>
        <CardTitle className="text-destructive">Danger zone</CardTitle>
        <CardDescription>
          Deleting your account removes your profile and your login permanently.
          This cannot be undone.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <Dialog open={isOpen} onOpenChange={setOpen}>
          <DialogTrigger
            render={<Button variant="destructive">Delete account</Button>}
          />
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Delete account</DialogTitle>
              <DialogDescription>
                This permanently deletes your account and profile, and cannot be
                undone. Enter your password to confirm.
              </DialogDescription>
            </DialogHeader>

            <DeleteAccountForm onSuccess={() => setOpen(false)} />
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
};
