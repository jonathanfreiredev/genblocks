"use client";

import { useState } from "react";

import { toast } from "@/components/ui/toast";
import { requestPasswordSetupAction } from "@/server/auth/auth.actions";
import { Button } from "../ui/button";

/**
 * Adds a password to an account that so far signed in only with Google.
 *
 * The password is not typed here: the user follows a link sent to the address
 * the account already has, which proves they control it. That reuses the same
 * recovery path as "forgot password" instead of trusting an open session with
 * a new credential.
 */
export const RequestPasswordSetup = ({ onSent }: { onSent?: () => void }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <p className="text-muted-foreground text-sm">
        We send a link to the address on this account. Follow it to choose a
        password; it is added to the same account, and you can keep signing in
        with Google.
      </p>

      <Button
        type="button"
        disabled={isSubmitting}
        onClick={async () => {
          setIsSubmitting(true);

          const res = await requestPasswordSetupAction();

          if (res?.serverError) {
            toast.add({
              title: "Could not send the link!",
              description: res.serverError.message,
              type: "error",
            });
            setIsSubmitting(false);
            return;
          }

          toast.add({
            title: "Check your email",
            description: "The link lets you set a password for this account.",
            type: "success",
          });

          onSent?.();
        }}
      >
        Send the link
      </Button>
    </div>
  );
};
