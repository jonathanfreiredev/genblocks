import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig, type Plugin } from "vite";

/**
 * Fontsource ships a `woff` fallback beside every `woff2`. Nothing that runs this
 * registry needs it, and the preview is one document, so the fallback would be
 * inlined as base64 beside the font it duplicates: a third more bytes per weight
 * for a browser that has not been current since IE11. Drop it before Vite reads
 * the stylesheet, so the file is never emitted either.
 */
function woff2Only(): Plugin {
  return {
    name: "genblocks:woff2-only",
    enforce: "pre",
    transform(code, id) {
      if (!id.includes("@fontsource") || !id.endsWith(".css")) return null;

      const stripped = code.replace(/,\s*url\([^)]*\.woff\)\s*format\(["']woff["']\)/g, "");

      return { code: stripped, map: null };
    },
  };
}

/**
 * How one generated block is bundled.
 *
 * `base: "./"` so the built page is the same whether it is served or opened off
 * the filesystem: the sandbox serves it, but a relative base is what makes the
 * bundle portable, and a bundle that only works behind one server would be a
 * weaker claim than the one being made.
 *
 * Tailwind is part of the scaffold because the blocks are written in it
 * (PLAN.md, decision 24): a render without the stylesheet would be a picture of
 * a page nobody would ever serve.
 */
export default defineConfig({
  base: "./",
  plugins: [woff2Only(), react(), tailwindcss()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    // The preview is one document, so a font is inlined as a data: URL rather
    // than emitted as a sibling file the inliner cannot carry. The policy already
    // allows `font-src data:`, and a latin weight is 13-23 KB, far under this.
    assetsInlineLimit: 512 * 1024,
    // One chunk, because the preview is one file: a dynamic import would become a
    // sibling request the inliner cannot carry, and a block that needs one is a
    // block whose page is slower to open than it is to copy.
    rollupOptions: { output: { codeSplitting: false } },
  },
});
