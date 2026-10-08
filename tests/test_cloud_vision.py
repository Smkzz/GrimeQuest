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
    _clean_text, _plausible_name, CLOUD_VISION_FIELDS
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
    assert req.url.params["fields"] == CLOUD_VISION_FIELDS
    assert list(req.url.params.keys()) == ["fields"]
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


def test_google_rejected_key_is_immediate_auth_error_not_a_fake_timeout():
    from server.cloud_vision import _provider_code
    secret = "VERY_PRIVATE_GOOGLE_ACCOUNT_MUST_NOT_SHOW"
    google_error = {"error":{
        "code":403,
        "status":"PERMISSION_DENIED",
        "message":secret,
        "details":[{"reason":"API_KEY_HTTP_REFERRER_BLOCKED",
                    "metadata":{"consumer":"projects/PRIVATE_PROJECT"}}]
    }}
    request_calls = []
    def forbidden(request):
        request_calls.append(request)
        return httpx.Response(403,json=google_error)
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(forbidden))
    with pytest.raises(CloudVisionUnavailable) as raised:
        asyncio.run(reader.read(image(),image()))
    assert raised.value.code=="HTTP_403_API_KEY_HTTP_REFERRER_BLOCKED"
    assert "server's API configuration" in str(raised.value)
    assert secret not in str(raised.value)
    assert KEY not in str(raised.value)
    assert len(request_calls)==1
    assert _provider_code(403,json.dumps(google_error).encode())=="HTTP_403_API_KEY_HTTP_REFERRER_BLOCKED"


def test_no_untrusted_provider_error_detail_can_be_logged():
    from server.cloud_vision import _provider_code
    text = {"error":{"status":"PERMISSION_DENIED",
                     "details":[{"reason":{"unexpected":"malicious object"}}],
                     "message":"SECRET PHOTO TEXT"}}
    assert _provider_code(403,json.dumps(text).encode())=="HTTP_403_PERMISSION_DENIED"
    assert _provider_code(403,b"not-json")=="HTTP_403"


def test_transient_google_failures_have_bounded_status_codes():
    for status in (400,401,403,404,429,500,503):
        reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(
            lambda req:httpx.Response(status,json={"error":{"message":"PRIVATE KEY"}})))
        with pytest.raises(CloudVisionUnavailable) as raised:
            asyncio.run(reader.read(image(),image()))
        assert raised.value.code==f"HTTP_{status}"
        assert "PRIVATE KEY" not in str(raised.value)


def test_one_shot_synthetic_proof_uses_real_batch_path_with_no_customer_photo():
    captures=[]
    reader=CloudVisionReader(KEY,PROJECT,transport=transport(response(),captures))
    assert asyncio.run(reader.synthetic_diagnostic())=="PASS_HTTP_200"
    assert len(captures)==1
    data=json.loads(captures[0].content)
    assert len(data["requests"])==2
    assert all(b"KIILTO" not in base64.b64decode(task["image"]["content"]) for task in data["requests"])
    assert KEY not in str(captures[0].url)


def test_synthetic_diagnostic_returns_sanitized_failed_status():
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(
        lambda req:httpx.Response(403,json={"error":{
            "details":[{"reason":"API_KEY_SERVICE_BLOCKED"}],
            "message":"private Google secret"
        }})))
    assert asyncio.run(reader.synthetic_diagnostic())=="HTTP_403_API_KEY_SERVICE_BLOCKED"


def test_google_partial_response_avoids_huge_symbol_geometry():
    """Google's dense unmasked OCR JSON exceeded the former 1.5 MB cap."""
    captured=[]
    def handle(request):
        captured.append(request)
        assert request.url.params.get("fields")==CLOUD_VISION_FIELDS
        assert "key" not in request.url.params
        # Mimic Google's server-side projection: only the combined text
        # and page confidence are returned, not millions of bounding vertices.
        return httpx.Response(200,json=response())
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(handle))
    out=asyncio.run(reader.read(image(),image()))
    assert out.label_readable and out.name=="KIILTO KOTI"
    assert len(captured)==1


def test_oversized_response_is_bounded_without_leaking_key_or_photo():
    """An upstream that ignores the fields filter must still fail safely."""
    calls=[]
    def handle(request):
        calls.append(request)
        return httpx.Response(200,json={"responses":response()["responses"],
            "unusedSymbolCoordinates":"X"*1_600_000})
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(handle))
    with pytest.raises(CloudVisionUnavailable) as exc:
        asyncio.run(reader.read(image(),image()))
    assert exc.value.code=="RESPONSE_TOO_LARGE"
    assert "KEY" not in str(exc.value) and KEY not in str(exc.value)
    assert len(calls)==1


def test_text_annotations_fallback_when_full_text_is_absent():
    fallback={"responses":[
        {"textAnnotations":[{"description":"KIILTO KOTI\nYleispuhdistussuihke"}]},
        {"fullTextAnnotation":{"text":"KÄYTTÖOHJE\nLue ohjeet ja varoitukset."}}
    ]}
    reader=CloudVisionReader(KEY,PROJECT,transport=httpx.MockTransport(
        lambda r:httpx.Response(200,json=fallback)))
    out=asyncio.run(reader.read(image(),image()))
    assert out.name=="KIILTO KOTI"
    assert out.label_readable is True

