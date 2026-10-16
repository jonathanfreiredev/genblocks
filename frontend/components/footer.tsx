/**
 * Site footer.
 *
 * A minimal chrome band: who wrote the code and where to find them, the current
 * year and the license it ships under. Deliberately plain so it can be restyled
 * without untangling it from the pages it wraps.
 */
export function Footer() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-border/70 text-muted-foreground mt-auto border-t px-6 py-4 text-xs">
      <div className="mx-auto flex w-full max-w-5xl flex-col items-center justify-between gap-2 sm:flex-row">
        <p>
          © {year}{" "}
          <a
            href="https://jonathanfreire.com"
            target="_blank"
            rel="noreferrer"
            className="hover:text-foreground underline underline-offset-4"
          >
            Jonathan Freire
          </a>
        </p>
        <p>
          Released under the{" "}
          <a
            href="https://github.com/jonathanfreiredev/mcp-stack/blob/main/LICENSE"
            target="_blank"
            rel="noreferrer"
            className="hover:text-foreground underline underline-offset-4"
          >
            MIT License
          </a>
        </p>
      </div>
    </footer>
  );
}
