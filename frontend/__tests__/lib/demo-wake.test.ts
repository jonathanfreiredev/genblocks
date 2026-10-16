import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";

import { probeDemoServices } from "@/lib/demo-wake";
import { server } from "../msw/server";

const WARMUP = "/api/warmup";

/**
 * The one question the page asks about the demo's services.
 *
 * Everything that is not a plain "they are up" has to come back as "waking": the page
 * polls on that answer, and a wrong "ready" would send a visitor into a run that cannot
 * finish.
 */
describe("probeDemoServices", () => {
  test("reports the demo ready when the answer says both services are up", async () => {
    server.use(http.get(WARMUP, () => HttpResponse.json({ ready: true })));

    await expect(probeDemoServices()).resolves.toBe("ready");
  });

  test("reports the demo waking while one of them is still coming up", async () => {
    server.use(http.get(WARMUP, () => HttpResponse.json({ ready: false })));

    await expect(probeDemoServices()).resolves.toBe("waking");
  });

  test("reports the demo waking when nothing answers", async () => {
    // A slept container the platform is still starting looks like this, and so does an
    // API that is not there at all.
    server.use(http.get(WARMUP, () => HttpResponse.error()));

    await expect(probeDemoServices()).resolves.toBe("waking");
  });

  test("reports the demo waking when the page's own route fails", async () => {
    server.use(http.get(WARMUP, () => new HttpResponse(null, { status: 502 })));

    await expect(probeDemoServices()).resolves.toBe("waking");
  });

  test("reports the demo waking when the body is not the shape it expects", async () => {
    server.use(http.get(WARMUP, () => HttpResponse.json({ api: "ok" })));

    await expect(probeDemoServices()).resolves.toBe("waking");
  });

  test("asks this app's own warm-up route", async () => {
    const reached: string[] = [];

    server.use(
      http.get(WARMUP, ({ request }) => {
        reached.push(new URL(request.url).pathname);
        return HttpResponse.json({ ready: true });
      }),
    );

    await probeDemoServices();

    expect(reached).toEqual([WARMUP]);
  });
});
