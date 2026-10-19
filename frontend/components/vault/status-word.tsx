import { Loader2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/**
 * A state, in a badge.
 *
 * A running operation carries one small spinner; failed borrows the destructive
 * pair; queued is quiet. The state is still a word, because a word is what a
 * checklist can be read for at a glance.
 */
export function StatusWord({
  label,
  running,
  failed,
  muted,
}: {
  label: string;
  running?: boolean;
  failed?: boolean;
  muted?: boolean;
}) {
  return (
    <Badge
      variant={failed ? "destructive" : running ? "secondary" : "outline"}
      className={cn("gap-1.5", muted && "text-muted-foreground")}
    >
      {running ? <Loader2 className="animate-spin" aria-hidden /> : null}
      {label}
    </Badge>
  );
}
