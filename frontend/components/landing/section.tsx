import { cn } from "@/lib/utils";

/**
 * Page section shell.
 *
 * Owns the page's rhythm: one max width, one hairline between sections, and more
 * air above a heading than under it.
 */
export function Section({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className={cn(
        "border-border/70 border-t px-4 py-24 sm:px-6 lg:px-8",
        className,
      )}
    >
      <div className="mx-auto w-full max-w-5xl">{children}</div>
    </section>
  );
}

export function SectionHeading({
  title,
  lead,
}: {
  title: string;
  lead?: string;
}) {
  return (
    <header className="mb-14 max-w-[62ch]">
      <h2 className="text-2xl font-semibold tracking-tight text-balance sm:text-3xl">
        {title}
      </h2>
      {lead ? (
        <p className="text-muted-foreground mt-4 text-base text-pretty">
          {lead}
        </p>
      ) : null}
    </header>
  );
}
