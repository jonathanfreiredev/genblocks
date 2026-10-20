"""Decode, bound and re-encode a picture before anybody else sees it.

The bytes that arrive from a provider or from a browser are not the bytes this
service stores. They can carry EXIF (a camera, a location, a person), an ICC
profile nobody needs, a decompression bomb or a format whose decoder is the
attack surface. The safety gate should see the picture the registry will serve,
not a richer original that only the provider knows how to write.

The rule is intentionally narrow: a still image in a format Pillow can decode,
under a pixel and byte bound, re-encoded to JPEG (no alpha) or PNG (alpha) with
no metadata. The result is what moderation scores, what the judge sees and what
Cloudinary stores.
"""

from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

from app.settings import settings

# Pillow's own guard is a second line behind the explicit pixel check. It is set
# from the production bound, not from a test's monkeypatched one: a test that
# lowers the setting must still exercise our check, and a deployment that raises
# it must not lose the decoder's protection.
Image.MAX_IMAGE_PIXELS = max(settings.image_max_pixels * 2, 50_000_000)

ALLOWED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})
JPEG_QUALITY_FLOOR = 55


class ImageRefused(Exception):
    """The bytes are not a picture this service will store."""


@dataclass(frozen=True)
class SanitizedImage:
    """A picture after decoding, orientation, metadata removal and re-encoding."""

    data: bytes
    media_type: str
    width: int
    height: int
    source_format: str


def sanitize_image(data: bytes, *, media_type: str = "image/jpeg") -> SanitizedImage:
    """Return a clean copy of ``data``, or refuse it with a reason.

    ``media_type`` is the provider's claim. It is kept only as a hint for the
    output choice; the decoder's actual format is what decides whether the bytes
    are acceptable.
    """
    if not data:
        raise ImageRefused("The picture is empty.")
    if len(data) > settings.image_max_bytes:
        raise ImageRefused(
            f"The picture is larger than the {settings.image_max_bytes:,}-byte limit."
        )

    try:
        with Image.open(BytesIO(data)) as probe:
            probe.verify()
    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as refused:
        raise ImageRefused("The picture is not a readable image.") from refused

    try:
        with Image.open(BytesIO(data)) as opened:
            source_format = (opened.format or "").upper()
            if source_format not in ALLOWED_FORMATS:
                raise ImageRefused(
                    f"The picture format {source_format or 'unknown'} is not allowed."
                )
            if getattr(opened, "is_animated", False):
                raise ImageRefused("Animated pictures are not accepted.")

            width, height = opened.size
            if width <= 0 or height <= 0:
                raise ImageRefused("The picture has no dimensions.")
            if width * height > settings.image_max_pixels:
                raise ImageRefused(
                    f"The picture is {width}×{height}, larger than the "
                    f"{settings.image_max_pixels:,}-pixel limit."
                )

            oriented = ImageOps.exif_transpose(opened)
            oriented.load()
            has_alpha = "A" in oriented.getbands() or "transparency" in oriented.info
            clean = oriented.convert("RGBA" if has_alpha else "RGB")
    except ImageRefused:
        raise
    except (
        OSError,
        ValueError,
        SyntaxError,
        Image.DecompressionBombError,
    ) as refused:
        raise ImageRefused("The picture could not be decoded safely.") from refused

    # ``media_type`` is only a hint. A PNG that arrived as ``image/jpeg`` still
    # becomes a PNG, because the alpha channel is part of the picture.
    return _encoded(clean, source_format=source_format, has_alpha=has_alpha)


def _encoded(image: Image.Image, *, source_format: str, has_alpha: bool) -> SanitizedImage:
    """Encode without metadata, and enforce the output byte bound."""
    if has_alpha:
        return _png(image, source_format=source_format)

    quality = settings.image_reencode_quality
    while True:
        buffer = BytesIO()
        image.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
        )
        data = buffer.getvalue()
        if len(data) <= settings.image_max_bytes:
            return SanitizedImage(
                data=data,
                media_type="image/jpeg",
                width=image.width,
                height=image.height,
                source_format=source_format,
            )
        if quality <= JPEG_QUALITY_FLOOR:
            raise ImageRefused(
                "The picture is still too large after re-encoding at the minimum quality."
            )
        quality -= 10


def _png(image: Image.Image, *, source_format: str) -> SanitizedImage:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    data = buffer.getvalue()
    if len(data) > settings.image_max_bytes:
        raise ImageRefused("The picture is still too large after re-encoding as PNG.")

    return SanitizedImage(
        data=data,
        media_type="image/png",
        width=image.width,
        height=image.height,
        source_format=source_format,
    )
