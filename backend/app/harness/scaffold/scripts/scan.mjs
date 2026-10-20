/**
 * The AST half of the sandbox's safety bar.
 *
 * The backend already reads the source as text before spending a container.
 * This runs inside the container, after the project has been written and (for
 * the bundle mode) after Vite has produced the bytes a browser will actually
 * execute. It parses both with TypeScript rather than matching lines, so a
 * comment that mentions `fetch(` is not a call and a URL assembled from pieces
 * is still a URL.
 *
 * Usage:
 *   node scripts/scan.mjs source
 *   node scripts/scan.mjs bundle
 *
 * A finding exits non-zero; the sandbox turns that into a fatal `ast` or
 * `bundle` check.
 */

import fs from "node:fs";
import path from "node:path";
import ts from "typescript";

const mode = process.argv[2] === "bundle" ? "bundle" : "source";
const root = process.cwd();
const findings = [];

const SOURCE_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx"]);
const URL_ATTRIBUTES = new Set(["src", "srcSet", "poster", "href", "action", "formAction", "ping"]);
const FORBIDDEN_TAGS = new Set([
  "script",
  "iframe",
  "object",
  "embed",
  "applet",
  "frame",
  "frameset",
  "base",
]);
const GLOBAL_OBJECTS = new Set([
  "window",
  "globalThis",
  "self",
  "document",
  "navigator",
  "top",
  "parent",
  "frames",
  "opener",
  "localStorage",
  "sessionStorage",
  "indexedDB",
  "process",
]);
const NETWORK_CALLS = new Set([
  "fetch",
  "eval",
  "importScripts",
  "require",
  "sendBeacon",
]);
const NETWORK_CONSTRUCTORS = new Set([
  "Function",
  "Image",
  "Audio",
  "WebSocket",
  "EventSource",
  "RTCPeerConnection",
  "webkitRTCPeerConnection",
  "WebTransport",
]);
const SAFE_BUNDLE_HOSTS = new Set([
  "www.w3.org",
  "react.dev",
  "reactjs.org",
  "res.cloudinary.com",
]);
// React's own preload polyfill contains one `fetch(`. A generated block that
// calls fetch adds a second, so the bundle scan compares against that baseline
// rather than treating the framework as a finding.
const BUNDLE_CALLS = new Set(["eval", "importScripts", "sendBeacon"]);
const REACT_FETCH_BASELINE = 1;
const BUNDLE_CONSTRUCTORS = new Set([
  "Function",
  "WebSocket",
  "EventSource",
  "RTCPeerConnection",
  "webkitRTCPeerConnection",
  "WebTransport",
]);

function filesIn(directory, extension) {
  if (!fs.existsSync(directory)) return [];
  const found = [];
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      found.push(...filesIn(full, extension));
    } else if (extension(full)) {
      found.push(full);
    }
  }
  return found;
}

function sourceFiles() {
  return filesIn(path.join(root, "src"), (file) => {
    if (!SOURCE_EXTENSIONS.has(path.extname(file))) return false;
    const relative = path.relative(root, file).split(path.sep).join("/");
    return relative !== "src/main.tsx" && relative !== "src/index.css";
  });
}

function bundleFiles() {
  return filesIn(
    path.join(root, "dist", "assets"),
    (file) => path.extname(file) === ".js" || path.extname(file) === ".css",
  );
}

function report(file, node, rule, message) {
  const source = node.getSourceFile();
  const position = source.getLineAndCharacterOfPosition(node.getStart(source));
  findings.push({
    file: path.relative(root, file),
    line: position.line + 1,
    column: position.character + 1,
    rule,
    message,
  });
}

function reportText(file, text, index, rule, message) {
  const before = text.slice(0, index);
  const line = before.split("\n").length;
  const column = index - before.lastIndexOf("\n");
  findings.push({
    file: path.relative(root, file),
    line,
    column,
    rule,
    message,
  });
}

function attributeName(attribute) {
  return attribute.name.getText(attribute.getSourceFile());
}

function literalText(node) {
  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
    return node.text;
  }
  return null;
}

function isTrue(node) {
  return node.kind === ts.SyntaxKind.TrueKeyword;
}

function scanSource(file, source) {
  const visit = (node) => {
    if (ts.isJsxAttribute(node)) {
      const name = attributeName(node);
      if (name === "dangerouslySetInnerHTML") {
        report(file, node, "html-injection", "uses dangerouslySetInnerHTML");
      }
      if (URL_ATTRIBUTES.has(name) && node.initializer) {
        if (ts.isStringLiteral(node.initializer)) {
          if (/^\s*javascript:/i.test(node.initializer.text)) {
            report(file, node, "javascript-url", "uses a javascript: URL");
          }
        } else if (ts.isJsxExpression(node.initializer) && node.initializer.expression) {
          const expression = node.initializer.expression;
          if (literalText(expression) === null) {
            report(file, node, "dynamic-url", `${name} is built at runtime`);
          } else if (/^\s*javascript:/i.test(literalText(expression))) {
            report(file, node, "javascript-url", "uses a javascript: URL");
          }
        }
      }
    }

    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const tag = node.tagName.getText(node.getSourceFile()).toLowerCase();
      if (FORBIDDEN_TAGS.has(tag)) {
        report(file, node, "forbidden-tag", `embeds <${tag}>`);
      }
    }

    if (ts.isCallExpression(node)) {
      const called = node.expression;
      if (called.kind === ts.SyntaxKind.ImportKeyword) {
        report(file, node, "dynamic-import", "uses a dynamic import");
      } else {
        const name = ts.isIdentifier(called) ? called.text : null;
        if (name && NETWORK_CALLS.has(name)) {
          report(file, node, "network-call", `calls ${name}`);
        }
        if (
          name &&
          (name === "setTimeout" || name === "setInterval") &&
          node.arguments.some((argument) => literalText(argument) !== null)
        ) {
          report(file, node, "string-timer", `runs ${name} with a string`);
        }
        if (ts.isPropertyAccessExpression(called)) {
          const owner = called.expression.getText(node.getSourceFile());
          const member = called.name.text;
          if (owner === "document" && (member === "write" || member === "writeln")) {
            report(file, node, "document-write", "writes markup with document.write");
          }
          if (GLOBAL_OBJECTS.has(owner)) {
            report(file, node, "browser-global", `reaches ${owner}.${member}`);
          }
        }
      }
    }

    if (ts.isNewExpression(node)) {
      const name = node.expression.getText(node.getSourceFile());
      if (NETWORK_CONSTRUCTORS.has(name)) {
        report(file, node, "network-constructor", `creates ${name}`);
      }
      if (name === "Function") {
        report(file, node, "code-from-string", "builds a function from a string");
      }
    }

    if (ts.isPropertyAccessExpression(node)) {
      const owner = node.expression.getText(node.getSourceFile());
      if (GLOBAL_OBJECTS.has(owner)) {
        report(file, node, "browser-global", `reaches ${owner}.${node.name.text}`);
      }
      if (node.name.text === "serviceWorker") {
        report(file, node, "service-worker", "uses a service worker");
      }
      if (owner === "location" || node.name.text === "location") {
        report(file, node, "navigation", "uses location");
      }
    }

    if (ts.isWhileStatement(node) && isTrue(node.expression)) {
      report(file, node, "infinite-loop", "loops while true");
    }
    if (ts.isDoStatement(node) && isTrue(node.expression)) {
      report(file, node, "infinite-loop", "loops until true");
    }
    if (ts.isForStatement(node) && node.condition === undefined) {
      report(file, node, "infinite-loop", "loops with no condition");
    }

    if (ts.isStringLiteral(node) && /^\s*javascript:/i.test(node.text)) {
      report(file, node, "javascript-url", "uses a javascript: URL");
    }

    ts.forEachChild(node, visit);
  };

  visit(source);
}

function externalHost(text) {
  try {
    const url = new URL(text);
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    return url.hostname.toLowerCase();
  } catch {
    return null;
  }
}

function scanBundle(file, source) {
  let fetchSites = 0;
  let firstFetch = null;

  const visit = (node) => {
    if (ts.isCallExpression(node)) {
      const called = node.expression;
      if (called.kind === ts.SyntaxKind.ImportKeyword) {
        report(file, node, "dynamic-import", "uses a dynamic import");
      } else if (ts.isIdentifier(called) && called.text === "fetch") {
        fetchSites += 1;
        firstFetch ??= node;
      } else if (ts.isIdentifier(called) && BUNDLE_CALLS.has(called.text)) {
        report(file, node, "network-call", `calls ${called.text}`);
      } else if (
        ts.isPropertyAccessExpression(called) &&
        called.name.text === "sendBeacon"
      ) {
        report(file, node, "network-call", "calls sendBeacon");
      }
    }

    if (ts.isNewExpression(node)) {
      const name = node.expression.getText(node.getSourceFile());
      if (BUNDLE_CONSTRUCTORS.has(name)) {
        report(file, node, "network-constructor", `creates ${name}`);
      }
    }

    if (ts.isStringLiteral(node)) {
      if (/^\s*javascript:/i.test(node.text)) {
        report(file, node, "javascript-url", "uses a javascript: URL");
      }
      const host = externalHost(node.text);
      if (host && !SAFE_BUNDLE_HOSTS.has(host)) {
        report(file, node, "external-origin", `loads from ${host}`);
      }
    }

    ts.forEachChild(node, visit);
  };

  visit(source);

  if (fetchSites > REACT_FETCH_BASELINE && firstFetch) {
    report(file, firstFetch, "network-call", "calls fetch");
  }
}

function scanCss(file, text) {
  const url = /url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"]*))\s*\)/gi;
  for (const match of text.matchAll(url)) {
    const value = (match[1] || match[2] || match[3] || "").trim();
    if (value.startsWith("data:") || value.startsWith("/") || !value.includes("//")) {
      continue;
    }
    const host = externalHost(value.startsWith("//") ? `https:${value}` : value);
    if (host && !SAFE_BUNDLE_HOSTS.has(host)) {
      reportText(file, text, match.index ?? 0, "external-origin", `loads from ${host}`);
    }
  }
}

const files = mode === "bundle" ? bundleFiles() : sourceFiles();
for (const file of files) {
  const text = fs.readFileSync(file, "utf8");
  if (path.extname(file) === ".css") {
    if (mode === "bundle") scanCss(file, text);
    continue;
  }

  const kind = path.extname(file) === ".js" ? ts.ScriptKind.JS : ts.ScriptKind.TSX;
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, kind);
  if (mode === "bundle") scanBundle(file, source);
  else scanSource(file, source);
}

if (findings.length > 0) {
  const lines = findings
    .slice(0, 20)
    .map((one) => `${one.file}:${one.line} ${one.rule}: ${one.message}`);
  console.error(lines.join("; "));
  process.exit(1);
}

console.log(`${mode}: no AST findings`);
