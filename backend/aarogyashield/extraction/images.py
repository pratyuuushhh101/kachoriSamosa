from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError


MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PIXELS = 16_000_000


class ImageInputError(ValueError):
    def __init__(self, code: str, status: int):
        self.code, self.status = code, status
        super().__init__(code)


def sanitize_image(data: bytes, content_type: str, max_bytes: int = MAX_IMAGE_BYTES) -> tuple[bytes, str]:
    if len(data) > min(max_bytes, MAX_IMAGE_BYTES):
        raise ImageInputError("UPLOAD_TOO_LARGE", 413)
    declared = {"image/png": "PNG", "image/jpeg": "JPEG"}.get(content_type.lower())
    if declared is None:
        raise ImageInputError("UNSUPPORTED_MEDIA", 415)
    signature = data.startswith(b"\x89PNG\r\n\x1a\n") if declared == "PNG" else data.startswith(b"\xff\xd8\xff")
    if not signature:
        raise ImageInputError("UNSUPPORTED_MEDIA", 415)
    try:
        with Image.open(BytesIO(data)) as image:
            if image.format != declared:
                raise ImageInputError("UNSUPPORTED_MEDIA", 415)
            width, height = image.size
            if width * height > MAX_PIXELS:
                raise ImageInputError("IMAGE_TOO_LARGE", 413)
            image.load()
            clean = ImageOps.exif_transpose(image).convert("RGB")
            output = BytesIO()
            fmt = "PNG" if declared == "PNG" else "JPEG"
            clean.save(output, format=fmt, optimize=True)
    except ImageInputError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ImageInputError("INVALID_IMAGE", 400) from None
    sanitized = output.getvalue()
    if len(sanitized) > MAX_IMAGE_BYTES:
        raise ImageInputError("UPLOAD_TOO_LARGE", 413)
    return sanitized, "image/png" if declared == "PNG" else "image/jpeg"
