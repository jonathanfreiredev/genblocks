import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

/**
 * What "linted" means for a generated block.
 *
 * Deliberately the library defaults: the point is to catch a hook called
 * conditionally or a name that goes nowhere, not to impose a house style on
 * code that is meant to be copied into someone else's project.
 */
export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  reactHooks.configs.flat.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      globals: { ...globals.browser },
    },
  },
);
