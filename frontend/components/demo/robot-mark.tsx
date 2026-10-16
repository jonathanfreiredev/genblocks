import { cn } from "@/lib/utils";

/**
 * The robot, redrawn as a line drawing.
 *
 * It is the character the project's icons carry, simplified so it can sit inside a
 * line of text in the page's own colour rather than on top of it as a picture.
 *
 * `asleep` closes the eyes, and that is the whole joke: the two states are the whole
 * story the wake-up tells.
 */
export function RobotMark({
  asleep = false,
  className,
}: {
  asleep?: boolean;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.5}
      strokeLinecap="round"
      aria-hidden="true"
      className={cn("size-4", className)}
    >
      <circle cx="12" cy="2.6" r="1.3" fill="currentColor" stroke="none" />
      <path d="M12 3.9v2" />
      <rect x="3.9" y="5.9" width="16.2" height="14.2" rx="4.2" />
      {asleep ? (
        <>
          <path d="M7.6 11.6h2.6" />
          <path d="M13.8 11.6h2.6" />
        </>
      ) : (
        <>
          <circle
            cx="8.9"
            cy="11.6"
            r="1.15"
            fill="currentColor"
            stroke="none"
          />
          <circle
            cx="15.1"
            cy="11.6"
            r="1.15"
            fill="currentColor"
            stroke="none"
          />
        </>
      )}
      <path d="M9 16.2h6" />
    </svg>
  );
}
