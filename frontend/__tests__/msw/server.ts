import { setupServer } from "msw/node";

/**
 * Shared MSW server. Test files add handlers per case with `server.use(...)`;
 * the lifecycle (listen / reset / close) is wired in `vitest.setup.ts`.
 */
export const server = setupServer();
