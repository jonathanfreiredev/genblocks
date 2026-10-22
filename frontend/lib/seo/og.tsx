/* eslint-disable @next/next/no-img-element -- Satori renders these strings, not the browser. */
import { readFile } from "node:fs/promises";
import path from "node:path";

import { ImageResponse } from "next/og";

import { SITE_ORIGIN } from "@/lib/site";
import { clampDescription } from "@/lib/seo/metadata";

export const OG_SIZE = { width: 1200, height: 630 };
export const OG_CONTENT_TYPE = "image/png";
export const OG_ALT =
  "GenBlocks — generated UI blocks and stock images, scored by an independent judge";

const MARK_CANDIDATES = [
  path.join(process.cwd(), "public", "brand", "genblocks-mark.png"),
  path.join(process.cwd(), "frontend", "public", "brand", "genblocks-mark.png"),
];

let markPromise: Promise<string | null> | null = null;

/** The mark as a data URI, so Satori never has to fetch the site itself. */
async function markDataUri(): Promise<string | null> {
  if (!markPromise) {
    markPromise = (async () => {
      for (const candidate of MARK_CANDIDATES) {
        try {
          const bytes = await readFile(/* turbopackIgnore: true */ candidate);
          return `data:image/png;base64,${bytes.toString("base64")}`;
        } catch (error) {
          if ((error as NodeJS.ErrnoException).code !== "ENOENT") {
            throw error;
          }
        }
      }

      return null;
    })();
  }

  return markPromise;
}

function cloudinaryOgUrl(publicId: string): string | null {
  const cloud = process.env.NEXT_PUBLIC_CLOUDINARY_CLOUD_NAME?.trim();

  if (!cloud) {
    return null;
  }

  const encoded = publicId
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");

  // Ask Cloudinary for one small, social-sized JPEG instead of downloading a
  // multi-megabyte original into the function on every request.
  return `https://res.cloudinary.com/${cloud}/image/upload/c_fill,w_840,h_840,q_auto,f_jpg/${encoded}`;
}

/** A remote artifact as a data URI, or null when the CDN cannot answer. */
export async function artifactDataUri(
  publicId: string | null,
): Promise<string | null> {
  if (!publicId) {
    return null;
  }

  const url = /^https?:\/\//i.test(publicId)
    ? publicId
    : cloudinaryOgUrl(publicId);

  if (!url) {
    return null;
  }

  try {
    const response = await fetch(url, {
      signal: AbortSignal.timeout(5000),
    });

    if (!response.ok) {
      return null;
    }

    const type = response.headers.get("content-type") ?? "image/jpeg";
    if (!type.startsWith("image/")) {
      return null;
    }

    const bytes = Buffer.from(await response.arrayBuffer());
    return `data:${type};base64,${bytes.toString("base64")}`;
  } catch {
    return null;
  }
}

export interface OgImageOptions {
  eyebrow: string;
  title: string;
  description?: string;
  /** A data URI, normally from `artifactDataUri`. */
  image?: string | null;
  /** A block render is wide; an image is usually portrait or square. */
  imageFit?: "cover" | "contain";
  footer?: string;
}

/**
 * The one social card composition.
 *
 * It follows the shell rather than inventing a second identity: white ground,
 * a hairline border, the orange mark beside the wordmark, and type from the
 * same neutral scale. The artifact, when there is one, sits in a square frame
 * on the right.
 */
export async function renderOgImage({
  eyebrow,
  title,
  description,
  image,
  imageFit = "cover",
  footer = "Generated. Scored. Ready to copy.",
}: OgImageOptions): Promise<ImageResponse> {
  const mark = await markDataUri();
  const hasImage = Boolean(image);
  const cleanTitle = clampDescription(title, 92);
  const cleanDescription = description
    ? clampDescription(description, 150)
    : undefined;

  return new ImageResponse(
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        boxSizing: "border-box",
        background: "#ffffff",
        color: "#0a0a0a",
        padding: "64px",
        fontFamily: "sans-serif",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          justifyContent: "space-between",
          gap: "40px",
        }}
      >
        <div
          style={{
            minWidth: 0,
            flex: 1,
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            {mark ? (
              <img
                src={mark}
                alt=""
                width={64}
                height={64}
                style={{ width: 64, height: 64, objectFit: "contain" }}
              />
            ) : null}
            <span
              style={{
                fontSize: 34,
                fontWeight: 600,
                letterSpacing: "-0.04em",
              }}
            >
              GenBlocks
            </span>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "18px",
              maxWidth: hasImage ? 580 : 900,
            }}
          >
            <span
              style={{
                fontSize: 18,
                fontWeight: 500,
                letterSpacing: "0.12em",
                textTransform: "uppercase",
                color: "#737373",
              }}
            >
              {eyebrow}
            </span>
            <span
              style={{
                fontSize: hasImage ? 54 : 68,
                fontWeight: 600,
                lineHeight: 1.05,
                letterSpacing: "-0.045em",
              }}
            >
              {cleanTitle}
            </span>
            {cleanDescription ? (
              <span
                style={{
                  fontSize: 24,
                  lineHeight: 1.35,
                  color: "#525252",
                }}
              >
                {cleanDescription}
              </span>
            ) : null}
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "24px",
              borderTop: "1px solid #e5e5e5",
              paddingTop: "18px",
              fontSize: 18,
              color: "#737373",
            }}
          >
            <span>{SITE_ORIGIN.replace(/^https?:\/\//, "")}</span>
            <span>{footer}</span>
          </div>
        </div>

        {hasImage ? (
          <div
            style={{
              width: 420,
              height: "100%",
              display: "flex",
              overflow: "hidden",
              border: "1px solid #e5e5e5",
              borderRadius: "20px",
              background: "#f5f5f5",
            }}
          >
            <img
              src={image!}
              alt=""
              style={{ width: "100%", height: "100%", objectFit: imageFit }}
            />
          </div>
        ) : null}
      </div>
    </div>,
    {
      ...OG_SIZE,
      // One stable alt string per file convention; the page metadata carries
      // the specific description.
    },
  );
}
