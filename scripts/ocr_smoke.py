"""Release-only smoke: real Finnish/English Tesseract on synthetic labels, no user files."""
import base64
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from server.images import normalize_image
from server.ocr import available, recognize_product

assert available(), "Finnish+English OCR binary/language packs unavailable"
font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
assert font_path.exists(), "Pinned smoke test font absent"
font = ImageFont.truetype(str(font_path), 39)

def photo(lines):
    image = Image.new("RGB", (1280, 490), "white")
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(lines):
        draw.text((28, 29 + index * 110), line, font=font, fill="black")
    buf = io.BytesIO()
    image.save(buf, "JPEG", quality=85)
    raw = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return normalize_image(raw).data_url

front = photo(["KIILTO KOTI", "Yleispuhdistussuihke", "Hajusteeton 600 ml"])
back = photo(["KÄYTTÖOHJE", "Suihkuta ja pyyhi.", "VAROITUS: Lue käyttöohje!"])
obs = recognize_product(front, back)
assert obs.label_readable, "Both sides should be readable"
assert "KIILTO KOTI" in obs.name, obs.name
assert "KÄYTTÖOHJE" in obs.label_text, "Finnish directions not recognized"
assert "VAROITUS" in obs.label_text, "Warnings not recognized"
assert obs.warnings_observed == [], "OCR must not interpret or recommend chemical use"
print("GQ_LOCAL_OCR_SMOKE_PASS")
