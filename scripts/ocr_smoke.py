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

# Exercise the actual HTTP route and request boundary with paid AI unconfigured.
from fastapi.testclient import TestClient
from server.app import create_app
from server.config import Settings

with TestClient(create_app(Settings())) as client:
    health = client.get("/api/health").json()
    assert health["label_ocr_ready"] is True
    assert health["live_ready"] is False
    body = {"front_image": front, "back_image": back, "consent": True}
    assert client.post("/api/read-labels", json=body,
                       headers={"origin": "https://untrusted.example"}).status_code == 403
    assert client.post("/api/read-labels", json={**body, "consent": False},
                       headers={"origin": "http://testserver"}).status_code == 422
    response = client.post("/api/read-labels", json=body,
                           headers={"origin": "http://testserver"})
    assert response.status_code == 200, response.text[:1000]
    payload = response.json()
    assert payload["review_status"] == "unreviewed"
    assert payload["recommendation_permission"] is False
    assert payload["provider_calls"] == 0
    assert "KIILTO KOTI" in payload["observation"]["name"]
    assert "data:image/" not in response.text
    print("GQ_LOCAL_OCR_API_SMOKE_PASS")

