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
# A phone-like photographed bottle is not a uniform block of text: graphics,
# curved container edge, high-contrast band, competing text sizes and tilt.
art=Image.new("RGB",(1200,1500),"#ddd4bb")
drawing=ImageDraw.Draw(art)
drawing.rounded_rectangle((190,140,1020,1370),radius=65,fill="#e7e4c5",outline="#747251",width=6)
drawing.rectangle((240,260,965,740),fill="#688887")
smaller=ImageFont.truetype(str(font_path),28)
drawing.text((330,360),"KIILTO KOTI",font=font,fill="#fafafa")
drawing.text((295,450),"Yleispuhdistussuihke",font=smaller,fill="#fafafa")
drawing.text((390,560),"Hajusteeton",font=smaller,fill="#fafafa")
drawing.text((350,820),"Puhdistaa likaa",font=smaller,fill="#303b27")
drawing.text((330,920),"VAROITUS: Lue ohjeet",font=smaller,fill="#303b27")
art=art.rotate(3,expand=False,fillcolor="#ddd4bb")
raw=io.BytesIO()
art.save(raw,"JPEG",quality=83)
art_data=normalize_image("data:image/jpeg;base64,"+base64.b64encode(raw.getvalue()).decode()).data_url
art_observation=recognize_product(art_data,back)
assert art_observation.name=="KIILTO KOTI",art_observation.name
assert art_observation.label_readable, "Artistic synthetic bottle should have enough legible text"

# Regression from the supplied phone screenshot: neither '| MTT' nor
# 'LSANYTOL | VS' is a confidently established product name.
from server.ocr import _parse_tsv, _name, NAME_UNREADABLE
header="level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
noise=header+"".join(
    f"5\t1\t1\t1\t{i}\t{j}\t{j*30}\t{i*40}\t28\t16\t90\t{word}\n"
    for i,line in enumerate(["| MTT","< - M","LSANYTOL | VS"],1)
    for j,word in enumerate(line.split(),1)
)
assert _name(_parse_tsv(noise.encode(),1200)) is None
assert NAME_UNREADABLE.startswith("Product name unclear")

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

# Fail-soft regression: on a CPU-starved host, BOTH engine invocations can
# exceed their per-photo deadline. Never propagate as an API 503; return 200
# with an explicitly unreadable, manual-editable result. No retries/provider.
import subprocess
from unittest.mock import patch
from server import ocr as _ocr

deadline_calls=[]
def _engine_timeout(argv, **kwargs):
    deadline_calls.append((argv, kwargs["timeout"]))
    raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

with patch.object(_ocr.subprocess, "run", side_effect=_engine_timeout):
    unfinished = recognize_product(front, back)
    assert unfinished.label_readable is False
    assert unfinished.name.startswith("Product name unclear")
    assert all(limit == 5.0 for _, limit in deadline_calls)
    assert len(deadline_calls) == 2, "One engine attempt per label, never four"
    with TestClient(create_app(Settings())) as client:
        response = client.post(
            "/api/read-labels",
            json={"front_image":front,"back_image":back,"consent":True},
            headers={"origin":"http://testserver"}
        )
        assert response.status_code == 200, response.text[:400]
        assert response.json()["observation"]["label_readable"] is False
        assert response.json()["recommendation_permission"] is False
    assert len(deadline_calls) == 4
    print("GQ_LOCAL_OCR_TIMEOUT_FALLBACK_PASS")

