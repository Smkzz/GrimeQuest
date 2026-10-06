"""Bounded decoding and re-encoding strips metadata; no uploaded file is written."""
import base64
import binascii
import hashlib
import io
import warnings
from dataclasses import dataclass
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 2_000_000
MAX_PIXELS = 12_000_000
MAX_EDGE = 1600

class InvalidImage(ValueError):
    pass

@dataclass(frozen=True)
class NormalizedImage:
    data_url: str
    digest: str
    width: int
    height: int


def normalize_image(value: str) -> NormalizedImage:
    if not isinstance(value, str) or len(value) > 2_800_000:
        raise InvalidImage("Image is too large")
    prefix, sep, encoded = value.partition(",")
    mime_format = {"data:image/jpeg;base64": "JPEG", "data:image/png;base64": "PNG", "data:image/webp;base64": "WEBP"}
    if not sep or prefix not in mime_format:
        raise InvalidImage("Only base64 JPEG, PNG and WebP images are supported")
    try:
        raw = base64.b64decode(encoded, validate=True)
        if not 32 <= len(raw) <= MAX_BYTES:
            raise InvalidImage("Image must be between 32 bytes and 2 MB")
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(raw)) as im:
                if im.format != mime_format[prefix]:
                    raise InvalidImage("Image content does not match its media type")
                if getattr(im, "n_frames", 1) != 1:
                    raise InvalidImage("Animated images are not supported")
                w, h = im.size
                if w < 64 or h < 64 or w * h > MAX_PIXELS:
                    raise InvalidImage("Image dimensions must be at least 64x64 and at most 12 megapixels")
                im.load()
                im = ImageOps.exif_transpose(im)
                # New pixel buffer and RGB conversion omit metadata and transparent content.
                rgb = Image.new("RGB", im.size, "white")
                if im.mode in ("RGBA", "LA") or "transparency" in im.info:
                    rgba = im.convert("RGBA")
                    rgb.paste(rgba, mask=rgba.getchannel("A"))
                else:
                    rgb.paste(im.convert("RGB"))
                rgb.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
                out = io.BytesIO()
                rgb.save(out, "JPEG", quality=85, optimize=True)
                clean = out.getvalue()
                return NormalizedImage("data:image/jpeg;base64," + base64.b64encode(clean).decode(), hashlib.sha256(clean).hexdigest(), *rgb.size)
    except InvalidImage:
        raise
    except (ValueError, OSError, binascii.Error, UnidentifiedImageError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise InvalidImage("Invalid or unsupported image") from exc
