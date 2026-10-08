"""Barcode-first inventory lookups, safe checksum and no-OCR gameplay fallback."""
import asyncio
import importlib
import json
import time

import httpx
import pytest
from fastapi.testclient import TestClient

from server.barcodes import BarcodeLookup, BarcodeSuggestion, valid_gtin, unknown
from server.config import Settings

VALID = "4006381333931"
ORIGIN = {"origin": "http://testserver"}


def ean(body):
    total=sum(int(ch)*(3 if i%2==0 else 1) for i,ch in enumerate(reversed(body)))
    return body + str((10-total%10)%10)


def test_real_gtin_check_digits_and_no_short_guessing():
    assert valid_gtin(VALID)
    assert valid_gtin("036000291452")
    assert valid_gtin("96385074")
    assert valid_gtin(ean("1234567890123"))
    for bad in ("", "123", "4006381333932", "abcd12345678", " 4006381333931 ",
                "12345678901", "123456789012345", "4006381333931\n"):
        assert not valid_gtin(bad),bad
    assert not valid_gtin(None)


def test_strict_community_lookup_has_no_photo_or_unapproved_safety_data():
    seen=[]
    def handler(request):
        seen.append(request)
        assert request.method=="GET"
        assert request.url.host=="world.openproductsfacts.org"
        assert request.url.path==f"/api/v2/product/{VALID}.json"
        assert request.url.params["fields"]=="code,product_name,product_name_fi,product_name_en,brands,quantity"
        assert request.headers["user-agent"].startswith("GrimeQuest/")
        assert "authorization" not in request.headers
        assert not request.content
        return httpx.Response(200,json={"status":1,"code":VALID,"product":{
            "product_name":"All-purpose cleaner",
            "product_name_fi":"Kiilto Koti",
            "brands":"Kiilto",
            "quantity":"600 ml",
            "warnings":"dangerous and unverified"
        }})
    suggestion=asyncio.run(BarcodeLookup(transport=httpx.MockTransport(handler)).lookup(VALID))
    assert suggestion.found
    assert suggestion.name=="Kiilto Koti"
    assert suggestion.brand=="Kiilto"
    assert suggestion.quantity=="600 ml"
    payload=suggestion.public()
    assert payload["review_status"]=="unreviewed"
    assert payload["recommendation_permission"] is False
    assert "warnings" not in payload and "hazards" not in payload
    assert payload["source_url"]=="https://world.openproductsfacts.org/product/"+VALID
    assert len(seen)==1


def test_unknown_product_or_missing_title_is_nonblocking():
    for reply in [
        {"status":0,"status_verbose":"product not found"},
        {"status":1,"code":VALID,"product":{"brands":"Some Brand"}},
        {"status":1,"code":"1111111111111","product":{"product_name":"Wrong barcode"}},
    ]:
        handler=httpx.MockTransport(lambda request:httpx.Response(200,json=reply))
        result=asyncio.run(BarcodeLookup(transport=handler).lookup(VALID))
        assert not result.found
        assert result.name==""
        assert result.public()["recommendation_permission"] is False


def test_remote_errors_redirects_or_giant_responses_fail_to_manual():
    for status in (301,302,403,429,500,503):
        reader=BarcodeLookup(transport=httpx.MockTransport(
            lambda request:httpx.Response(status,headers={"location":"https://evil.example"})))
        assert not asyncio.run(reader.lookup(VALID)).found
    giant=BarcodeLookup(transport=httpx.MockTransport(
        lambda request:httpx.Response(200,content=b"x"*90_000)))
    assert not asyncio.run(giant.lookup(VALID)).found
    broken=BarcodeLookup(transport=httpx.MockTransport(
        lambda request:(_ for _ in ()).throw(httpx.ConnectError("network unreachable",request=request))))
    assert not asyncio.run(broken.lookup(VALID)).found
    with pytest.raises(ValueError):
        asyncio.run(BarcodeLookup().lookup("4006381333932"))


def test_local_product_lookup_requires_no_private_ai_key_and_no_image():
    events=[]
    class Index:
        async def lookup(self,barcode):
            events.append(barcode)
            return BarcodeSuggestion(barcode,True,"Kiilto Koti","Kiilto","600 ml")
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(Settings(),barcode_lookup=Index())) as client:
        response=client.post("/api/product-lookup",json={"barcode":VALID},headers=ORIGIN)
        assert response.status_code==200,response.text
        result=response.json()
        assert result["found"] is True
        assert result["name"]=="Kiilto Koti"
        assert result["recommendation_permission"] is False
        assert result["review_status"]=="unreviewed"
        assert "data:image" not in response.text
        assert events==[VALID]
        # Identical code uses short server cache and never hammers OPF.
        assert client.post("/api/product-lookup",json={"barcode":VALID},headers=ORIGIN).status_code==200
        assert events==[VALID]


def test_public_barcode_endpoint_rejects_cross_origin_and_bad_check_digits():
    events=[]
    class Index:
        async def lookup(self,barcode):
            events.append(barcode)
            return unknown(barcode)
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(Settings(),barcode_lookup=Index())) as client:
        assert client.post("/api/product-lookup",json={"barcode":VALID},
          headers={"origin":"https://attacker.example"}).status_code==403
        assert client.post("/api/product-lookup",json={"barcode":"4006381333932"},
          headers=ORIGIN).status_code==422
        assert client.post("/api/product-lookup",json={"barcode":"<img>"},
          headers=ORIGIN).status_code==422
        assert client.post("/api/product-lookup",json={"barcode":VALID,"image":"x"},
          headers=ORIGIN).status_code==422
        assert events==[]


def test_rate_limit_blocks_remote_requests_without_stopping_manual_gameplay():
    calls=[]
    class Index:
        async def lookup(self,barcode):
            calls.append(barcode)
            return unknown(barcode)
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(Settings(),barcode_lookup=Index())) as client:
        client.app.state.barcode_requests.extend([time.monotonic()]*8)
        code=ean("641123456789")
        r=client.post("/api/product-lookup",json={"barcode":code},headers=ORIGIN)
        assert r.status_code==429
        assert not calls
        assert "Enter the product name manually" in r.text
