from io import BytesIO

import pytest
from PIL import Image

from app.images import sanitize
from app.images.sanitize import ImageRefused, sanitize_image
from app.settings import settings


def encoded(*, mode: str = "RGB", size: tuple[int, int] = (48, 32), exif: bool = False) -> bytes:
    image = Image.new(mode, size, "red")
    buffer = BytesIO()
    kwargs = {"format": "JPEG"}
    if exif:
        exif_bytes = Image.Exif()
        exif_bytes[0x010E] = "a private caption"
        exif_bytes[0x0132] = "2026:10:20 12:00:00"
        kwargs["exif"] = exif_bytes
    image.save(buffer, **kwargs)
    return buffer.getvalue()


def test_a_picture_is_reencoded_without_its_metadata():
    source = encoded(exif=True)

    clean = sanitize_image(source, media_type="image/jpeg")

    with Image.open(BytesIO(clean.data)) as picture:
        assert picture.format == "JPEG"
        assert dict(picture.getexif()) == {}
        assert "a private caption" not in clean.data.decode("latin-1")
    assert clean.media_type == "image/jpeg"
    assert (clean.width, clean.height) == (48, 32)


def test_a_png_with_alpha_stays_png():
    image = Image.new("RGBA", (20, 20), (255, 0, 0, 120))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    clean = sanitize_image(buffer.getvalue(), media_type="image/png")

    with Image.open(BytesIO(clean.data)) as picture:
        assert picture.format == "PNG"
        assert picture.mode == "RGBA"
    assert clean.media_type == "image/png"


def test_a_picture_over_the_pixel_bound_is_refused(monkeypatch):
    monkeypatch.setattr(settings, "image_max_pixels", 100)

    with pytest.raises(ImageRefused, match="pixel"):
        sanitize_image(encoded(size=(20, 20)))


def test_a_picture_over_the_byte_bound_is_refused(monkeypatch):
    monkeypatch.setattr(settings, "image_max_bytes", 10)

    with pytest.raises(ImageRefused, match="MB limit|larger"):
        sanitize_image(encoded())


def test_an_animated_picture_is_refused():
    image = Image.new("RGB", (20, 20), "red")
    frames = [image, Image.new("RGB", (20, 20), "blue")]
    buffer = BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:])

    with pytest.raises(ImageRefused, match="not a readable|format"):
        sanitize_image(buffer.getvalue())


def test_bytes_that_are_not_a_picture_are_refused():
    with pytest.raises(ImageRefused, match="readable"):
        sanitize_image(b"not an image")


def test_the_module_has_a_real_pillow_guard():
    assert Image.MAX_IMAGE_PIXELS is not None
    assert {"JPEG", "PNG", "WEBP"} == sanitize.ALLOWED_FORMATS
