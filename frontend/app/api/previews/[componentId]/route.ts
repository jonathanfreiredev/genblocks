import { env } from "@/lib/env";
import { PREVIEW_CSP } from "@/lib/vault/preview";

/** A block id, so a bad address costs no round trip. */
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * A block's built page, as the browser that embeds it should receive it.
 *
 * The API holds the document and hands it over as text; this route is the one
 * place it is served as a page, and the policy that comes with it is the reason
 * that is safe. Without the `sandbox` directive an iframe attribute would be the only
 * fence, and somebody opening this address in a tab would run generated code on
 * this origin — with the visitor's session cookies in reach. With it, the page is
 * on an opaque origin whether it is embedded or opened directly.
 *
 * `no-store` on purpose: blocks can be taken down, and a cached document would
 * outlive the takedown in a browser or a proxy. The document is a few hundred
 * kilobytes and the block's pictures are the expensive part of the page.
 */
export async function GET(
  _request: Request,
  { params }: { params: Promise<{ componentId: string }> },
) {
  const { componentId } = await params;

  if (!UUID.test(componentId)) {
    return new Response(null, { status: 404 });
  }

  let upstream: Response;

  try {
    upstream = await fetch(
      new URL(`/v1/components/${componentId}/preview`, env.BACKEND_URL),
      { cache: "no-store" },
    );
  } catch {
    return new Response(null, { status: 502 });
  }

  if (!upstream.ok) {
    return new Response(null, { status: upstream.status === 404 ? 404 : 502 });
  }

  // A block may only reach our own Cloudinary account, not every customer's:
  // the static check makes that claim about the source, and this makes it true
  // for a URL the page builds at runtime. The trailing slash is the whole
  // difference between allowing the account and allowing one path: a source with
  // a path matches that path exactly, so `/cloud` blocked every picture under
  // `/cloud/image/upload/...`.
  const cloud = env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME;
  const pictures = cloud
    ? `https://res.cloudinary.com/${cloud}/`
    : "https://res.cloudinary.com";
  const policy = PREVIEW_CSP.replace("https://res.cloudinary.com", pictures);

  return new Response(await upstream.text(), {
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": policy,
      // The policy above is the fence; these are the usual companions to it.
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      "Permissions-Policy":
        "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
      "Cache-Control": "no-store",
    },
  });
}
