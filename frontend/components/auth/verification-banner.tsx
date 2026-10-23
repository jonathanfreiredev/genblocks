"use client";
import { useState } from "react";
import { toast } from "@/components/ui/toast";
import { Button } from "../ui/button";
import { resendVerificationEmail } from "@/server/auth/session.actions";

export const VerificationBanner = () => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  return (
    <div className="flex items-center justify-center gap-1 border-b border-amber-200 bg-amber-50 px-4 py-2 text-sm text-amber-900">
      <span>Your email is not verified yet.</span>
      <Button
        variant="link"
        className="h-auto p-0"
        disabled={isSubmitting}
        onClick={async () => {
          setIsSubmitting(true);
          const res = await resendVerificationEmail();
          setIsSubmitting(false);

          if (!res.success) {
            toast.add({
              title: "Could not resend",
              description: res.message,
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
