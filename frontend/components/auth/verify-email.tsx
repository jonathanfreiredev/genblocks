"use client";
import Link from "next/link";
import { useState } from "react";

import { toast } from "@/components/ui/toast";
import { requestVerificationEmailAction } from "@/server/auth/auth.actions";
import { Button } from "../ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "../ui/card";
import { FieldDescription } from "../ui/field";

export const VerifyEmail = ({ email }: { email?: string }) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  return (
    <Card className="w-full max-w-125">
      <CardHeader className="text-center">
        <CardTitle className="text-xl">Verify your email</CardTitle>
        <CardDescription>Your account was created successfully</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center gap-4">
        <FieldDescription className="text-center">
          {email
            ? `We sent a verification link to ${email}. Open it to confirm your email — the link signs you in automatically.`
            : "We sent you a verification link. Open it to confirm your email — the link signs you in automatically."}
        </FieldDescription>

        {email ? (
          <Button
            type="button"
            variant="outline"
            disabled={isSubmitting}
            onClick={async () => {
              if (!email) {
                return;
              }

              setIsSubmitting(true);
              const res = await requestVerificationEmailAction({ email });
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
        ) : null}

        <Link href="/auth/login">
          <Button variant="link">Go to log in</Button>
        </Link>
      </CardContent>
    </Card>
  );
};
