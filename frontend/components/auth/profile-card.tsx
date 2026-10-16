"use client";

import { useState } from "react";

import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import { Field, FieldGroup, FieldTitle } from "../ui/field";
import { ChangePasswordForm } from "./change-password-form";
import { ProfileEditForm } from "./profile-edit-form";

/**
 * The profile card. It reads rather than edits: the details are shown and the two
 * things that change them each open their own dialog.
 *
 * Nothing here is editable in place on purpose. This page is mostly visited to
 * look, and an always-open form invites half-finished edits that were never
 * saved and are not visible as such.
 */
export const ProfileCard = ({
  user,
}: {
  user: { name: string; email: string };
}) => {
  const [isEditOpen, setEditOpen] = useState(false);
  const [isChangePasswordOpen, setChangePasswordOpen] = useState(false);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">My profile</CardTitle>
        <CardDescription>Your name and email address.</CardDescription>
      </CardHeader>

      <CardContent>
        <FieldGroup>
          <Field>
            <FieldTitle>Name</FieldTitle>
            <p className="text-sm">{user.name || "—"}</p>
          </Field>
          <Field>
            <FieldTitle>Email</FieldTitle>
            <p className="text-sm">{user.email || "—"}</p>
          </Field>
        </FieldGroup>
      </CardContent>

      <CardFooter className="flex justify-end gap-2">
        <Dialog open={isEditOpen} onOpenChange={setEditOpen}>
          <DialogTrigger render={<Button>Edit profile</Button>} />
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Edit profile</DialogTitle>
              <DialogDescription>
                Change your name, or the email you sign in with.
              </DialogDescription>
            </DialogHeader>

            <ProfileEditForm user={user} onSuccess={() => setEditOpen(false)} />
          </DialogContent>
        </Dialog>

        <Dialog
          open={isChangePasswordOpen}
          onOpenChange={setChangePasswordOpen}
        >
          <DialogTrigger
            render={<Button variant="outline">Change password</Button>}
          />
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Change password</DialogTitle>
              <DialogDescription>
                Enter your new password below to change your password.
              </DialogDescription>
            </DialogHeader>

            <ChangePasswordForm
              onSuccess={() => setChangePasswordOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </CardFooter>
    </Card>
  );
};
