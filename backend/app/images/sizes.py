"""The sizes the image provider accepts.

Kept out of ``app.harness.images`` so a process that only plans an image (the MCP
server) can check a request without importing Pillow or any provider client.
"""

SIZE_STEP = 32
MIN_SIDE = 256
MAX_SIDE = 1536


def size_complaint(width: int, height: int) -> str | None:
    """Why a size cannot be generated, or ``None`` when it can."""
    for side, name in ((width, "width"), (height, "height")):
        if side % SIZE_STEP:
            return f"{name} must be a multiple of {SIZE_STEP} (asked for {side})."
        if not MIN_SIDE <= side <= MAX_SIDE:
            return f"{name} must be between {MIN_SIDE} and {MAX_SIDE} (asked for {side})."

    return None
