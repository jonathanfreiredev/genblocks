import { Separator } from "@/components/ui/separator";

/**
 * The visual break between the two ways into an account.
 *
 * Rendered only when both providers are enabled. The text stays in the
 * accessibility tree so the relationship reads as "Google, or email", while
 * the rules are decorative.
 */
export function AuthDivider() {
  return (
    <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3">
      <Separator aria-hidden="true" />
      <span className="text-muted-foreground text-xs">or</span>
      <Separator aria-hidden="true" />
    </div>
  );
}
