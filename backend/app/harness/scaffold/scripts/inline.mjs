/**
 * Turn the built page into one file a host can hand to a browser.
 *
 * The sandbox already serves `dist/` over loopback to photograph it. That page is
 * the block, exactly as it was built — so the registry shows the same bytes as a
 * live preview instead of rebuilding the project somewhere else. One file, for
 * three reasons:
 *
 * - It has no sibling requests: the JS and the CSS travel with the document, so
 *   a host can serve it from one response without a static tree beside it.
 * - It can be embedded without a URL: an iframe with `srcdoc`, or a response with
 *   a `sandbox` policy, keeps the block on an opaque origin.
 * - It cannot be edited into something else on the way: what is stored is what
 *   was built.
 *
 * The policy and the bridge are injected here, not in `index.html`, so `vite
 * build` keeps producing an ordinary project a person can inspect.
 *
 * Usage: node scripts/inline.mjs (after `vite build`)
 */

import fs from "node:fs";
import path from "node:path";

const dist = path.join(process.cwd(), "dist");
const source = path.join(dist, "index.html");
const target = path.join(dist, "preview.html");

/**
 * What the preview may reach.
 *
 * `script-src 'unsafe-inline'` is the price of one file: the bundle is the
 * document. Everything else is closed — no network, no form requests, no nested
 * frames, no external styles — and the pictures are the one thing a block is
 * allowed to ask Cloudinary for.
 */
const POLICY = [
  "default-src 'none'",
  "script-src 'unsafe-inline'",
  "style-src 'unsafe-inline'",
  "img-src https://res.cloudinary.com data:",
  "font-src data:",
  "connect-src 'none'",
  "form-action 'none'",
  "frame-src 'none'",
  "object-src 'none'",
  "base-uri 'none'",
].join("; ");

/**
 * The host's half of the contract, inside the document.
 *
 * It runs before the bundle so the first paint already has the theme the library
 * is in; afterwards it follows changes over `postMessage`. It also reports the
 * page's height so the frame is as tall as the block, and it stops a link from
 * navigating the frame away from the block.
 */
const BRIDGE = `<script>
(() => {
  const root = document.documentElement;

  const apply = (theme) => {
    const dark = theme === "dark";
    root.classList.toggle("dark", dark);
    root.style.colorScheme = dark ? "dark" : "light";
  };

  apply(new URLSearchParams(location.search).get("theme") === "dark" ? "dark" : "light");

  addEventListener("message", (event) => {
    const message = event.data;
    if (!message || message.type !== "genblocks:preview") return;
    if (message.theme === "dark" || message.theme === "light") apply(message.theme);
  });

  let queued = 0;
  const tell = () => {
    if (!document.body) return;

    cancelAnimationFrame(queued);
    queued = requestAnimationFrame(() => {
      const height = Math.ceil(
        Math.max(document.body.scrollHeight, root.scrollHeight),
      );
      parent.postMessage({ type: "genblocks:preview:size", height }, "*");
    });
  };

  // The bridge travels in the head, before the document has a body: the theme
  // can be applied there, but observing the page and catching clicks cannot.
  const start = () => {
    new ResizeObserver(tell).observe(document.body);

    // A block is a demonstration, not a destination: a link stays where it is.
    addEventListener(
      "click",
      (event) => {
        const anchor =
          event.target instanceof Element
            ? event.target.closest("a[href]")
            : null;
        if (anchor) event.preventDefault();
      },
      true,
    );

    tell();
  };

  if (document.readyState === "loading") {
    addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

  addEventListener("load", tell);
})();
</script>`;

/** One asset referenced by the built page, read from `dist/`. */
function asset(href) {
  const file = path.join(dist, href.replace(/^\.?\//, ""));

  if (!file.startsWith(dist + path.sep) || !fs.existsSync(file)) {
    throw new Error(`The built page points at something that is not in dist: ${href}`);
  }

  return fs.readFileSync(file, "utf8");
}

/**
 * A `</script>` inside a string would close the tag early. Escaping the slash is
 * valid JavaScript in a string, a template or a regular expression, and it is the
 * one edit that keeps the document parseable.
 */
function scriptSafe(code) {
  return code.replace(/<\/script/gi, "<\\/script");
}

/** A `</style>` inside a CSS string would end the stylesheet early. */
function styleSafe(css) {
  return css.replace(/<\/style/gi, "<\\/style");
}

function inline(html) {
  const withoutPreloads = html.replace(
    /<link\b[^>]*\brel=["']modulepreload["'][^>]*>\s*/gi,
    "",
  );

  const withStyles = withoutPreloads.replace(
    /<link\b[^>]*\brel=["']stylesheet["'][^>]*>/gi,
    (tag) => {
      const href = /\bhref=["']([^"']+)["']/i.exec(tag)?.[1];
      if (!href) throw new Error("A stylesheet in the built page has no href.");

      return `<style>${styleSafe(asset(href))}</style>`;
    },
  );

  return withStyles.replace(
    /<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>\s*<\/script>/gi,
    (_, src) => `<script type="module">${scriptSafe(asset(src))}</script>`,
  );
}

function main() {
  if (!fs.existsSync(source)) {
    throw new Error("There is no dist/index.html: build before inlining.");
  }

  let html = inline(fs.readFileSync(source, "utf8"));
  const head = [
    `<meta http-equiv="Content-Security-Policy" content="${POLICY}">`,
    `<meta name="robots" content="noindex">`,
    BRIDGE,
  ].join("");

  if (!/<head[^>]*>/i.test(html)) {
    throw new Error("The built page has no head to put the policy in.");
  }

  html = html.replace(/<head[^>]*>/i, (tag) => `${tag}${head}`);

  if (/\b(?:src|href)=["'](?:\.\/)?assets\//i.test(html)) {
    throw new Error("An asset was left outside the document.");
  }

  fs.writeFileSync(target, html, "utf8");
  process.stdout.write(`preview: ${target} (${Buffer.byteLength(html)} bytes)\n`);
}

main();
