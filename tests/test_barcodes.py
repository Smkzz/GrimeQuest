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


def test_barcode_lookup_falls_through_worldwide_categories():
    """Products in Beauty Facts must work without a Finnish-specific catalog."""
    hosts=[]
    def responder(request):
        hosts.append(request.url.host)
        if request.url.host == "world.openbeautyfacts.org":
            return httpx.Response(200,json={"status":1,"code":VALID,"product":{
                "product_name":"Global Dish Soap","brands":"Worldwide Co",
                "quantity":"500 ml","unsafe_advice":"do not import"
            }})
        return httpx.Response(200,json={"status":0})
    finder=BarcodeLookup(transport=httpx.MockTransport(responder))
    match=asyncio.run(finder.lookup(VALID)).public()
    assert hosts==["world.openproductsfacts.org","world.openbeautyfacts.org"]
    assert match["source"]=="Open Beauty Facts"
    assert match["category"]=="beauty"
    assert match["source_url"]=="https://world.openbeautyfacts.org/product/"+VALID
    assert match["name"]=="Global Dish Soap"
    assert "unsafe_advice" not in match
    assert match["recommendation_permission"] is False


def test_international_name_search_across_four_official_sources():
    from server.barcodes import PLATFORMS
    query="洗衣粉"  # Genuine international character/script handling.
    seen=[]
    payloads={
        "world.openproductsfacts.org":{"products":[{"code":VALID,
           "product_name":"洗衣粉","brands":"Global Brand","quantity":"1 kg"}]},
        "world.openbeautyfacts.org":{"products":[{"code":"036000291452",
           "product_name":"Global Soap","brands":"Brand International"}]},
        "world.openfoodfacts.org":{"products":[{"code":"96385074",
           "product_name":"Baking Soda","brands":"Food Brand"}]},
        "world.openpetfoodfacts.org":{"products":[]},
    }
    def responder(request):
        seen.append((request.url.host,request.url.path,str(request.url.params.get("search_terms"))))
        assert request.method=="GET"
        assert request.url.path=="/cgi/search.pl"
        assert request.url.params["search_terms"]==query
        assert request.url.params["page_size"]=="8"
        assert request.url.params["json"]=="1"
        assert request.url.params["action"]=="process"
        assert request.url.params["fields"]=="code,product_name,product_name_en,product_name_fi,brands,quantity"
        assert request.headers["user-agent"].startswith("GrimeQuest/")
        assert "authorization" not in request.headers
        assert not request.content
        return httpx.Response(200,json=payloads[request.url.host])
    results=asyncio.run(BarcodeLookup(transport=httpx.MockTransport(responder)).search(query))
    assert len(seen)==len(PLATFORMS)==4
    assert len(results)==3
    assert results[0].name=="洗衣粉"
    assert {r.category for r in results}=={"general","beauty","food"}
    assert all(r.public()["recommendation_permission"] is False for r in results)
    assert all(r.public()["source_url"].startswith("https://world.open") for r in results)


def test_search_excludes_corrupt_barcodes_and_untrusted_external_links():
    malicious=[
        {"code":"4006381333932","product_name":"Wrong checksum"},
        {"code":VALID,"product_name":"<script>alert(1)</script>",
         "product_url":"https://evil.example/checkout"},
        {"code":VALID,"product_name":"Duplicate title"},
        {"code":"123","product_name":"Short identifier"},
    ]
    def responder(request):
        if request.url.host=="world.openproductsfacts.org":
            return httpx.Response(200,json={"products":malicious})
        return httpx.Response(200,json={"products":[]})
    result=asyncio.run(BarcodeLookup(transport=httpx.MockTransport(responder)).search("cleaner"))
    assert len(result)==1
    assert result[0].barcode==VALID
    assert "evil.example" not in str(result[0].public())
    assert result[0].public()["source_url"]=="https://world.openproductsfacts.org/product/"+VALID


def test_worldwide_search_api_is_public_but_origin_checked_and_rate_limited():
    calls=[]
    class Index:
        async def search(self,term):
            calls.append(term)
            from server.barcodes import BarcodeSuggestion
            return [BarcodeSuggestion(VALID,True,"Lysol Cleaner","Lysol","500 ml")]
        async def lookup(self,barcode):
            return unknown(barcode)
    m=importlib.import_module("server.app")
    with TestClient(m.create_app(Settings(),barcode_lookup=Index())) as client:
        r=client.post("/api/product-search",json={"query":"Lysol"},headers=ORIGIN)
        assert r.status_code==200,r.text
        data=r.json()
        assert data["source"]=="Open Facts"
        assert data["recommendation_permission"] is False
        assert data["results"][0]["name"]=="Lysol Cleaner"
        assert calls==["Lysol"]
        # Exact request cache prevents repeated upstream calls.
        assert client.post("/api/product-search",json={"query":"Lysol"},headers=ORIGIN).status_code==200
        assert calls==["Lysol"]
        # Only same-origin requests; no accepted photos or unknown fields.
        assert client.post("/api/product-search",json={"query":"Lysol"},headers={"origin":"https://evil.example"}).status_code==403
        assert client.post("/api/product-search",json={"query":"Lysol","image":"photo"},headers=ORIGIN).status_code==422
        assert client.post("/api/product-search",json={"query":"!"},headers=ORIGIN).status_code==422
        client.app.state.search_requests.extend([time.monotonic()]*5)
        blocked=client.post("/api/product-search",json={"query":"Cif"},headers=ORIGIN)
        assert blocked.status_code==429
        assert calls==["Lysol"]


def test_community_search_handles_four_outages_without_blocking_entry():
    finder=BarcodeLookup(transport=httpx.MockTransport(
        lambda req:httpx.Response(503,content=b"temporary downstream outage")))
    assert asyncio.run(finder.search("Any Brand"))==[]
    from server.barcodes import normalize_query
    assert normalize_query("洗衣粉")=="洗衣粉"
    assert normalize_query("Crème     Nettoyant")=="Crème Nettoyant"
    for invalid in ("", " ", "!", "a"*73):
        with pytest.raises(ValueError):
            normalize_query(invalid)

