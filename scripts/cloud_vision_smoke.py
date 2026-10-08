"""No-network Google Cloud Vision REST qualification. No real key or billed call."""
import base64
import io
import json
import time

import httpx
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from server.app import create_app
from server.config import Settings
from server.cloud_vision import CloudVisionReader, CloudVisionUnavailable, NAME_UNREADABLE
from server.images import normalize_image


KEY = "AIzaTEST_ONLY_NOT_A_REAL_KEY_0123456789abcdef"
PROJECT = "grimequest-test-project"
ORIGIN = "http://testserver"
calls = []


def photo(label):
    canvas = Image.new("RGB", (640, 440), "white")
    ImageDraw.Draw(canvas).text((20, 30), label, fill="black")
    memory = io.BytesIO()
    canvas.save(memory, "JPEG", quality=84)
    return normalize_image("data:image/jpeg;base64," + base64.b64encode(memory.getvalue()).decode()).data_url


front = photo("KIILTO KOTI")
back = photo("KAYTTOOHJE Lue ohjeet ja varoitukset")
items = [
    {"fullTextAnnotation": {"text": "KIILTO KOTI\nYleispuhdistussuihke\n",
                             "pages": [{"confidence": 0.97}]}},
    {"fullTextAnnotation": {"text": "KÄYTTÖOHJE\nLue ohjeet ja varoitukset ennen käyttöä.\n",
                             "pages": [{"confidence": 0.94}]}},
]


def handler(request):
    assert request.method == "POST"
    assert request.url.host == "eu-vision.googleapis.com"
    assert request.url.path == f"/v1/projects/{PROJECT}/locations/eu/images:annotate"
    assert not request.url.query, "No key in URL or logs"
    assert request.headers["x-goog-api-key"] == KEY
    assert "authorization" not in request.headers
    data = json.loads(request.content)
    assert len(data["requests"]) == 2
    assert [r["features"][0]["type"] for r in data["requests"]] == [
        "TEXT_DETECTION", "DOCUMENT_TEXT_DETECTION"
    ]
    for task in data["requests"]:
        raw = base64.b64decode(task["image"]["content"], validate=True)
        assert raw[:3] == b"\xff\xd8\xff"
        assert 32 <= len(raw) <= 2_000_000
        assert task["imageContext"]["languageHints"] == ["fi", "en"]
    calls.append(1)
    return httpx.Response(200, json={"responses": items})


reader = CloudVisionReader(KEY, PROJECT, transport=httpx.MockTransport(handler))
assert reader.ready
config = Settings(google_vision_enabled=True, google_vision_api_key=KEY,
                  google_vision_project_id=PROJECT)
with TestClient(create_app(config, label_reader=reader)) as client:
    health = client.get("/api/health").json()
    assert health["live_ready"] is False
    assert health["label_ocr_ready"] is True
    assert health["label_ocr_processor"] == "google_cloud_vision"
    body = {"front_image": front, "back_image": back, "consent": True}
    assert client.post("/api/read-labels", json=body,
                       headers={"origin": "https://attacker.example"}).status_code == 403
    assert client.post("/api/read-labels", json={**body, "consent": False},
                       headers={"origin": ORIGIN}).status_code == 422
    assert client.post("/api/read-labels", json={**body, "front_image": "bad"},
                       headers={"origin": ORIGIN}).status_code == 422
    assert not calls
    response = client.post("/api/read-labels", json=body, headers={"origin": ORIGIN})
    assert response.status_code == 200, response.text[:500]
    result = response.json()
    assert result["observation"]["name"] == "KIILTO KOTI"
    assert result["observation"]["label_readable"] is True
    assert "KÄYTTÖOHJE" in result["observation"]["label_text"]
    assert result["review_status"] == "unreviewed"
    assert result["recommendation_permission"] is False
    assert result["extraction"] == "google_cloud_vision"
    assert result["provider_calls"] == 1
    assert len(calls) == 1  # One external batch, never retry.
    assert KEY not in response.text and "data:image" not in response.text
    print("GQ_GOOGLE_VISION_CONSENTED_API_MOCK_PASS")

    # Billing cap in process; same-origin allowed and no provider request.
    client.app.state.ocr_calls.extend([time.monotonic()] * 12)
    denied = client.post("/api/read-labels", json=body, headers={"origin": ORIGIN})
    assert denied.status_code == 429
    assert len(calls) == 1
    print("GQ_GOOGLE_VISION_QUOTA_MOCK_PASS")

with TestClient(create_app(Settings())) as client:
    assert client.get("/api/health").json()["label_ocr_ready"] is False
    response = client.post("/api/read-labels",
                           json={"front_image": front, "back_image": back, "consent": True},
                           headers={"origin": ORIGIN})
    assert response.status_code == 503
    assert "server" not in response.text.lower() or "Enter the label manually" in response.text
    assert KEY not in response.text
    print("GQ_GOOGLE_VISION_DISABLED_SAFE_PASS")


def deny(request):
    assert request.headers["x-goog-api-key"] == KEY
    return httpx.Response(403, json={"error": {"message": "private-credentials-never-expose"}})


badreader = CloudVisionReader(KEY, PROJECT, transport=httpx.MockTransport(deny))
with TestClient(create_app(config, label_reader=badreader)) as client:
    response = client.post("/api/read-labels",
                           json={"front_image": front, "back_image": back, "consent": True},
                           headers={"origin": ORIGIN})
    assert response.status_code == 503
    assert "private-credentials" not in response.text and KEY not in response.text
    print("GQ_GOOGLE_VISION_SECRET_FAIL_CLOSED_PASS")

garbage = [{"fullTextAnnotation": {"text": "| MTT\nLSANYTOL | VS\n"}},
           {"fullTextAnnotation": {"text": ""}}]


def noisy(request):
    return httpx.Response(200, json={"responses": garbage})


noise = CloudVisionReader(KEY, PROJECT, transport=httpx.MockTransport(noisy))
with TestClient(create_app(config, label_reader=noise)) as client:
    result = client.post("/api/read-labels",
                         json={"front_image": front, "back_image": back, "consent": True},
                         headers={"origin": ORIGIN})
    assert result.status_code == 200
    assert result.json()["observation"]["name"] == NAME_UNREADABLE
    assert result.json()["observation"]["label_readable"] is False
    assert result.json()["recommendation_permission"] is False
    print("GQ_GOOGLE_VISION_GARBAGE_REJECTED_PASS")

print("GQ_GOOGLE_VISION_MOCK_QUALIFICATION_PASS")
