import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

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
  plugins: [react(), tailwindcss()],
  build: { outDir: "dist", emptyOutDir: true },
});
