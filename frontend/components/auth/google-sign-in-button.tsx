"use client";
import { useState } from "react";

import { toast } from "@/components/ui/toast";
import { signInWithGoogleAction } from "@/server/auth/auth.actions";
import { Button } from "../ui/button";

/**
 * Google's four-color G, kept as an inline asset so the button has no extra
 * network request and the mark stays crisp at any density. These brand colors
 * are intentionally literal; they are the identity of the provider, not theme
 * colors.
 */
function GoogleMark() {
  return (
    <svg
      viewBox="0 0 24 24"
      className="size-4"
      aria-hidden="true"
      focusable="false"
      data-icon="inline-start"
    >
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47a5.53 5.53 0 0 1-2.4 3.58v3h3.88c2.27-2.09 3.54-5.17 3.54-8.82Z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3c-1.08.72-2.45 1.16-4.05 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09A11.99 11.99 0 0 0 12 24Z"
      />
      <path
        fill="#FBBC05"
        d="M5.27 14.29A7.2 7.2 0 0 1 4.89 12c0-.8.14-1.57.38-2.29V6.62H1.29A11.99 11.99 0 0 0 0 12c0 1.93.46 3.76 1.29 5.38l3.98-3.09Z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.69 1.29 6.62l3.98 3.09C6.22 6.86 8.87 4.75 12 4.75Z"
      />
    </svg>
  );
}

export const GoogleSignInButton = ({
  className,
  next,
}: {
  className?: string;
  /** Path to return to after signing in. Validated by the action. */
  next?: string;
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  return (
    <Button
      type="button"
      variant="outline"
      className={className}
      disabled={isSubmitting}
      onClick={async () => {
        setIsSubmitting(true);
        const res = await signInWithGoogleAction({ next });

        if (res?.serverError) {
          toast.add({
            title: "Google sign-in failed!",
            description: res.serverError.message,
            type: "error",
          });
          setIsSubmitting(false);
          return;
        }

        if (res?.data?.url) {
          window.location.assign(res.data.url);
        }
      }}
    >
      <GoogleMark />
      Continue with Google
    </Button>
  );
};
