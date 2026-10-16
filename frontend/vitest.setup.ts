import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";

import { server } from "./__tests__/msw/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

afterEach(() => {
  // RTL only auto-cleans with `globals: true`, which this project does not use.
  cleanup();
  server.resetHandlers();
});

afterAll(() => server.close());
