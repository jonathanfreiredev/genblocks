/**
 * Turn the error body returned by the FastAPI backend into a display string.
 *
 * FastAPI uses `detail` for both `HTTPException` (a string) and request
 * validation errors (a list of `{ msg }` objects). Anything else falls back to
 * the caller's default, so the UI always receives a string.
 */
export function backendErrorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim() !== "") {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) =>
      item && typeof item === "object" && "msg" in item
        ? [String((item as { msg: unknown }).msg)]
        : [],
    );

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallback;
}
