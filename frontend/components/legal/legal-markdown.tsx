import Link from "next/link";
import type { ReactNode } from "react";

/**
 * The small Markdown subset the legal documents use.
 *
 * The assistant's renderer is a client component built for streaming answers.
 * A legal notice is static text: sending Streamdown and its parser to every
 * visitor cost more main-thread time than the notice itself, so this server
 * renderer handles the headings, lists, links, emphasis and code spans the
 * documents actually contain.
 */
function inline(source: string, keyPrefix: string): ReactNode[] {
  const parts = source.split(/(\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*[^*]+\*\*)/g);

  return parts.filter(Boolean).map((part, index) => {
    const key = `${keyPrefix}-${index}`;

    const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
    if (link) {
      const [, label, href] = link;

      if (href.startsWith("/")) {
        return (
          <Link key={key} href={href}>
            {label}
          </Link>
        );
      }

      return (
        <a
          key={key}
          href={href}
          {...(href.startsWith("http") ? { rel: "noreferrer" } : {})}
        >
          {label}
        </a>
      );
    }

    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={key}>{part.slice(1, -1)}</code>;
    }

    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={key}>{part.slice(2, -2)}</strong>;
    }

    return <span key={key}>{part}</span>;
  });
}

function paragraph(lines: string[], key: string): ReactNode {
  const children: ReactNode[] = [];

  lines.forEach((line, index) => {
    const hardBreak = line.endsWith("\\");
    const text = hardBreak ? line.slice(0, -1) : line;

    if (index > 0) {
      children.push(" ");
    }

    children.push(...inline(text, `${key}-${index}`));

    if (hardBreak) {
      children.push(<br key={`${key}-br-${index}`} />);
    }
  });

  return <p key={key}>{children}</p>;
}

export function LegalMarkdown({ source }: { source: string }) {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const blocks: ReactNode[] = [];
  let index = 0;
  let block = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (line.trim() === "") {
      index += 1;
      continue;
    }

    if (line.startsWith("### ")) {
      blocks.push(<h3 key={`h3-${block++}`}>{inline(line.slice(4), "h3")}</h3>);
      index += 1;
      continue;
    }

    if (line.startsWith("## ")) {
      blocks.push(<h2 key={`h2-${block++}`}>{inline(line.slice(3), "h2")}</h2>);
      index += 1;
      continue;
    }

    if (line.startsWith("# ")) {
      blocks.push(<h1 key={`h1-${block++}`}>{inline(line.slice(2), "h1")}</h1>);
      index += 1;
      continue;
    }

    if (line.trim() === "---") {
      blocks.push(<hr key={`hr-${block++}`} />);
      index += 1;
      continue;
    }

    if (/^[-*] /.test(line)) {
      const items: string[] = [];

      while (index < lines.length && /^[-*] /.test(lines[index])) {
        items.push(lines[index].slice(2));
        index += 1;
      }

      blocks.push(
        <ul key={`ul-${block++}`}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{inline(item, `ul-${block}-${itemIndex}`)}</li>
          ))}
        </ul>,
      );
      continue;
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = [];

      while (index < lines.length && /^\d+\. /.test(lines[index])) {
        items.push(lines[index].replace(/^\d+\. /, ""));
        index += 1;
      }

      blocks.push(
        <ol key={`ol-${block++}`}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{inline(item, `ol-${block}-${itemIndex}`)}</li>
          ))}
        </ol>,
      );
      continue;
    }

    const paragraphLines: string[] = [];

    while (index < lines.length && lines[index].trim() !== "") {
      if (
        paragraphLines.length > 0 &&
        (/^#{1,3} /.test(lines[index]) ||
          /^[-*] /.test(lines[index]) ||
          /^\d+\. /.test(lines[index]) ||
          lines[index].trim() === "---")
      ) {
        break;
      }

      paragraphLines.push(lines[index]);
      index += 1;
    }

    blocks.push(paragraph(paragraphLines, `p-${block++}`));
  }

  return <>{blocks}</>;
}
