from io import BytesIO

import pytest
from PIL import Image

from aarogyashield.extraction.images import ImageInputError, sanitize_image
from conftest import png_bytes


def test_valid_png_and_jpeg():
    png, kind = sanitize_image(png_bytes(), "image/png")
    assert kind == "image/png" and png.startswith(b"\x89PNG")
    out = BytesIO(); Image.new("RGB", (8, 8), "white").save(out, "JPEG")
    jpeg, kind = sanitize_image(out.getvalue(), "image/jpeg")
    assert kind == "image/jpeg" and jpeg.startswith(b"\xff\xd8\xff")


def test_spoofed_mime_rejected():
    with pytest.raises(ImageInputError):
        sanitize_image(png_bytes(), "image/jpeg")


def test_over_size_and_pixel_limit():
    with pytest.raises(ImageInputError) as error:
        sanitize_image(png_bytes(), "image/png", max_bytes=10)
    assert error.value.status == 413
    huge = BytesIO(); Image.new("RGB", (4001, 4000)).save(huge, "PNG")
    with pytest.raises(ImageInputError):
        sanitize_image(huge.getvalue(), "image/png")


def test_exif_removed():
    image = Image.new("RGB", (8, 8), "white")
    exif = Image.Exif(); exif[270] = "synthetic metadata"
    data = BytesIO(); image.save(data, "JPEG", exif=exif)
    result, _ = sanitize_image(data.getvalue(), "image/jpeg")
    with Image.open(BytesIO(result)) as clean:
        assert not clean.getexif()


def test_invalid_bytes_rejected():
    with pytest.raises(ImageInputError):
        sanitize_image(b"not an image", "image/png")
