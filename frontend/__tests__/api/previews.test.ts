// @vitest-environment node
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";

import { GET } from "@/app/api/previews/[componentId]/route";
import { server } from "../msw/server";

const BACKEND_URL = "http://backend.test";
const COMPONENT_ID = "0199f1ab-2c3d-4e5f-8a9b-0c1d2e3f4a5b";
const DOCUMENT =
  "<!doctype html><html><body><section>Sunset</section></body></html>";

function call(componentId: string) {
  return GET(new Request(`http://localhost/api/previews/${componentId}`), {
    params: Promise.resolve({ componentId }),
  });
}

describe("the preview route", () => {
  test("serves the block as a sandboxed document", async () => {
    server.use(
      http.get(
        `${BACKEND_URL}/v1/components/${COMPONENT_ID}/preview`,
        () =>
          new HttpResponse(DOCUMENT, {
            headers: { "Content-Type": "text/html" },
          }),
      ),
    );

    const response = await call(COMPONENT_ID);
    const policy = response.headers.get("content-security-policy") ?? "";

    expect(response.status).toBe(200);
    expect(await response.text()).toBe(DOCUMENT);
    // The document is generated code: it runs, but on an origin of its own and
    // with nowhere to send what a visitor types.
    expect(policy).toContain("sandbox allow-scripts allow-forms");
    expect(policy).not.toContain("allow-same-origin");
    expect(policy).toContain("connect-src 'none'");
    expect(policy).toContain("form-action 'none'");
    expect(policy).toContain("https://res.cloudinary.com/test-cloud");
    expect(response.headers.get("x-content-type-options")).toBe("nosniff");
    expect(response.headers.get("cache-control")).toBe("no-store");
  });

  test("answers a missing block with a missing document", async () => {
    server.use(
      http.get(
        `${BACKEND_URL}/v1/components/${COMPONENT_ID}/preview`,
        () => new HttpResponse(null, { status: 404 }),
      ),
    );

    expect((await call(COMPONENT_ID)).status).toBe(404);
  });

  test("does not ask the API for an address that is not an id", async () => {
    // No handler is installed: an unhandled request fails the test, which is the
    // assertion — the regex rejects the address before the round trip.
    expect((await call("not-a-uuid")).status).toBe(404);
  });

  test("says the API is unwell when it cannot answer", async () => {
    server.use(
      http.get(
        `${BACKEND_URL}/v1/components/${COMPONENT_ID}/preview`,
        () => new HttpResponse(null, { status: 500 }),
      ),
    );

    expect((await call(COMPONENT_ID)).status).toBe(502);
  });
});
