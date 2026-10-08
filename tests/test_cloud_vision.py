"""Cloud Vision OCR uses consent, EU-hosted API-key auth and fail-closed quotas."""
import asyncio
import base64
import importlib
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from server.cloud_vision import (
    CloudVisionReader, CloudVisionUnavailable, NAME_UNREADABLE,
    _clean_text, _plausible_name
)
from server.config import Settings
from conftest import make_image

KEY = "AIzaNONPROD_MOCK_CLOUD_VISION_KEY_abcdefghijk"
PROJECT = "grimequest-test-project"
ORIGIN = {"origin": "http://testserver"}


def transport(result, captures):
    def handler(request):
        captures.append(request)
        return httpx.Response(200, json=result)
    return httpx.MockTransport(handler)


def response(front="KIILTO KOTI\nYleispuhdistussuihke", back="KÄYTTÖOHJE\nLue käyttöohje ja varoitukset."):
    return {"responses": [
        {"fullTextAnnotation": {"text": front, "pages": [{"confidence": 0.95}]}},
        {"fullTextAnnotation": {"text": back, "pages": [{"confidence": 0.94}]}}
    ]}


def settings():
    return Settings(google_vision_enabled=True, google_vision_api_key=KEY,
                    google_vision_project_id=PROJECT)


def image():
    return make_image(size=(320, 240))


def body():
    return {"front_image": image(), "back_image": image(), "consent": True}


def test_api_key_is_only_in_private_http_header_and_batch_is_correct():
    captures = []
    reader = CloudVisionReader(KEY, PROJECT, transport=transport(response(), captures))
    assert reader.ready
    result = asyncio.run(reader.read(image(), image()))
    assert result.name == "KIILTO KOTI"
    assert result.label_readable
    assert "KÄYTTÖOHJE" in result.label_text
    assert result.warnings_observed == []
    assert len(captures) == 1
    req = captures[0]
    assert req.url.host == "eu-vision.googleapis.com"
    assert f"/projects/{PROJECT}/locations/eu/images:annotate" in req.url.path
    assert KEY not in str(req.url)
    assert req.headers["x-goog-api-key"] == KEY
    assert "authorization" not in req.headers
    tasks = json.loads(req.content)["requests"]
    assert [r["features"][0]["type"] for r in tasks] == ["TEXT_DETECTION", "DOCUMENT_TEXT_DETECTION"]
    assert all(r["imageContext"]["languageHints"] == ["fi", "en"] for r in tasks)
    assert all(base64.b64decode(r["image"]["content"]).startswith(b"\xff\xd8\xff") for r in tasks)


def test_no_config_no_google_api_key_not_ready_and_manual_fallback():
    with TestClient(importlib.import_module("server.app").create_app(Settings())) as client:
        health = client.get("/api/health").json()
        assert health["label_ocr_ready"] is False
        assert health["label_ocr_processor"] == "disabled"
        assert health["live_ready"] is False
        response = client.post("/api/read-labels", json=body(), headers=ORIGIN)
        assert response.status_code == 503
        assert "key" not in response.text.lower()


def test_valid_cloud_config_requires_explicit_opt_in():
    assert CloudVisionReader(KEY, PROJECT).ready
    assert not CloudVisionReader("short", PROJECT).ready
    assert not CloudVisionReader(KEY, "../outside").ready
    m=importlib.import_module("server.app")
    disabled=Settings(google_vision_api_key=KEY,google_vision_project_id=PROJECT,google_vision_enabled=False)
    with TestClient(m.create_app(disabled)) as c:
        assert c.get("/api/health").json()["label_ocr_ready"] is False


def test_public_cloud_ocr_needs_same_origin_and_real_boolean_consent():
    captured = []
    reader = CloudVisionReader(KEY, PROJECT, transport=transport(response(), captured))
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(settings(), label_reader=reader)) as client:
        assert client.get("/api/health").json()["label_ocr_ready"] is True
        assert client.get("/api/health").json()["live_ready"] is False
        assert client.post("/api/read-labels",json=body(),headers={"origin":"https://evil.example"}).status_code == 403
        assert client.post("/api/read-labels",json={**body(),"consent":False},headers=ORIGIN).status_code == 422
        assert client.post("/api/read-labels",json={**body(),"consent":1},headers=ORIGIN).status_code == 422
        assert client.post("/api/read-labels",json={**body(),"front_image":"x"},headers=ORIGIN).status_code == 422
        assert not captured
        ok = client.post("/api/read-labels",json=body(),headers=ORIGIN)
        assert ok.status_code == 200,ok.text
        assert ok.json()["extraction"] == "google_cloud_vision"
        assert ok.json()["provider_calls"] == 1
        assert ok.json()["review_status"] == "unreviewed"
        assert ok.json()["recommendation_permission"] is False
        assert "data:image" not in ok.text
        assert len(captured) == 1


def test_cloud_ocr_single_instance_rate_limit_stops_before_provider():
    captures = []
    reader=CloudVisionReader(KEY,PROJECT,transport=transport(response(),captures))
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(settings(),label_reader=reader)) as client:
        client.app.state.ocr_calls.extend([time.monotonic()] * 12)
        blocked = client.post("/api/read-labels", json=body(), headers=ORIGIN)
        assert blocked.status_code == 429
        assert not captures


def test_cloud_errors_are_sanitized_and_no_automatic_retry():
    captured=[]
    def fail(request):
        captured.append(request)
        return httpx.Response(403, json={"error":{"message":"SENSITIVE UPSTREAM DETAIL"}})
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(fail))
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(settings(),label_reader=reader)) as client:
        failed=client.post("/api/read-labels",json=body(),headers=ORIGIN)
        assert failed.status_code == 503
        assert "SENSITIVE" not in failed.text
        assert KEY not in failed.text
    assert len(captured) == 1


def test_garbled_text_never_becomes_product_name():
    captured = []
    reader = CloudVisionReader(KEY, PROJECT, transport=transport(
        response(front="| MTT\nLSANYTOL | VS", back=""), captured))
    result = asyncio.run(reader.read(image(), image()))
    assert result.name == NAME_UNREADABLE
    assert result.label_readable is False
    assert "UNVERIFIED" in result.label_text
    assert result.warnings_observed == []


def test_low_google_page_confidence_blocks_name_suggestion():
    data = response()
    data["responses"][0]["fullTextAnnotation"]["pages"][0]["confidence"] = 0.20
    reader = CloudVisionReader(KEY, PROJECT, transport=httpx.MockTransport(
        lambda req: httpx.Response(200,json=data)))
    result = asyncio.run(reader.read(image(),image()))
    assert result.name == NAME_UNREADABLE
    assert result.label_readable is False


def test_ocr_input_and_response_limits_and_incomplete_batch():
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(
        lambda req:httpx.Response(200,json={"responses":[{}]})))
    with pytest.raises(CloudVisionUnavailable):
        asyncio.run(reader.read(image(),image()))
    with pytest.raises(CloudVisionUnavailable):
        asyncio.run(reader.read("data:image/png;base64,AAA",image()))
    assert _clean_text("Hello\x00 World\n\nNext") == "Hello World\nNext"
    assert _plausible_name("| MTT\nLSANYTOL | VS", None) is None


def test_provider_transport_failure_has_generic_error():
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(
        lambda req: (_ for _ in ()).throw(httpx.ConnectError("secret host",request=req))))
    with pytest.raises(CloudVisionUnavailable) as exc:
        asyncio.run(reader.read(image(),image()))
    assert "secret" not in str(exc.value)
