/** Shiki grammar per file extension; anything else is shown as plain text. */
export const LANGUAGE_BY_EXTENSION: Record<string, string> = {
  css: "css",
  html: "html",
  js: "javascript",
  jsx: "jsx",
  json: "json",
  md: "markdown",
  mdx: "markdown",
  py: "python",
  sh: "bash",
  sql: "sql",
  ts: "typescript",
  tsx: "tsx",
  yaml: "yaml",
  yml: "yaml",
};

export function languageFor(path: string): string {
  const extension = path.slice(path.lastIndexOf(".") + 1).toLowerCase();

  return LANGUAGE_BY_EXTENSION[extension] ?? "text";
}
