"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

/**
 * Route-level error boundary. Errors thrown while rendering a page show this
 * fallback instead of the browser's default error page.
 */
export default function Error({
  error,
  unstable_retry,
}: {
  error: Error & { digest?: string };
  unstable_retry: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-16 text-center">
      <h1 className="text-2xl font-semibold">Something went wrong</h1>
      <p className="text-muted-foreground max-w-md text-sm">
        An unexpected error occurred. You can try again, or come back later.
      </p>
      <Button onClick={() => unstable_retry()}>Try again</Button>
    </div>
  );
}
