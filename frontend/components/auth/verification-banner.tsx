"use client";
import { useState } from "react";
import { toast } from "@/components/ui/toast";
import { Button } from "../ui/button";
import { resendVerificationAction } from "@/server/auth/auth.actions";

export const VerificationBanner = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  return (
    <div className="bg-amber-50 border-amber-200 text-amber-900 flex items-center justify-center gap-1 border-b px-4 py-2 text-sm">
      <span>Your email is not verified yet.</span>
      <Button
        variant="link"
        className="h-auto p-0"
        disabled={isSubmitting}
        onClick={async () => {
          setIsSubmitting(true);
          const res = await resendVerificationAction();
          setIsSubmitting(false);

          if (res?.serverError) {
            toast.add({
              title: "Could not resend",
              description: res.serverError.message,
              type: "error",
            });
            return;
          }

          toast.add({
            title: "Verification email sent",
            description: "Check your inbox for the verification link.",
            type: "success",
          });
        }}
      >
        Resend verification email
      </Button>
    </div>
  );
};
