"""A readable slug for a picture.

The asset path is a Cloudinary public id. A seeded picture keeps a descriptive
last segment (``bench-at-dusk``); a generated one is a hash, so its slug comes
from the prompt with a short piece of that hash to keep it unique.
"""

import re

# A prompt can be a paragraph; the slug only needs enough of it to be read.
STEM_LIMIT = 60

# The shape of the random names Cloudinary gives generated assets.
HASH = re.compile(r"^[0-9a-f]{16,}$")


def _words(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def image_slug(*, prompt: str, path: str) -> str:
    """The slug a picture is addressed by, from its prompt and its asset path."""
    tail = _words(path.rsplit("/", 1)[-1])

    # A descriptive id is already the best slug there is: a seeded asset was named
    # for the scene, not for its bytes.
    if tail and not HASH.match(tail):
        return tail

    stem = _words(prompt)[:STEM_LIMIT].strip("-")

    if stem and tail:
        return f"{stem}-{tail[:6]}"

    return stem or tail or "image"
