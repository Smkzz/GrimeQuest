"""No-network qualification: worldwide product name + barcode fallback."""
import asyncio

import httpx
from fastapi.testclient import TestClient

from server.app import create_app
from server.barcodes import BarcodeLookup, PLATFORMS, valid_gtin
from server.config import Settings

GOOD = "4006381333931"
UPC = "036000291452"
calls = []


def handler(request):
    calls.append(request)
    assert request.method == "GET"
    assert request.headers["user-agent"].startswith("GrimeQuest/")
    assert "authorization" not in request.headers
    assert request.content == b""
    if request.url.path == "/cgi/search.pl":
        assert request.url.params["search_terms"] == "洗衣粉"
        assert request.url.params["page_size"] == "8"
        assert request.url.params["fields"].startswith("code,product_name")
        if request.url.host == "world.openproductsfacts.org":
            return httpx.Response(200,json={"products":[{
                "code": GOOD, "product_name":"洗衣粉",
                "brands":"World Brand", "quantity":"500 g",
                "unsafe_instructions":"DO_NOT_IMPORT",
            }]})
        if request.url.host == "world.openbeautyfacts.org":
            return httpx.Response(200,json={"products":[{
                "code": UPC, "product_name":"Global Soap",
                "brands":"World Brand","quantity":"250 ml",
            }]})
        return httpx.Response(200,json={"products":[]})
    if request.url.path == "/api/v2/product/" + GOOD + ".json":
        if request.url.host == "world.openbeautyfacts.org":
            return httpx.Response(200,json={"status":1,"code":GOOD,"product":{
                "product_name":"World Cleanser","brands":"Universal"
            }})
        return httpx.Response(200,json={"status":0})
    raise AssertionError("An unexpected endpoint was requested")


reader = BarcodeLookup(transport=httpx.MockTransport(handler))
assert valid_gtin(GOOD) and valid_gtin(UPC)
with TestClient(create_app(Settings(), barcode_lookup=reader)) as client:
    origin = {"origin":"http://testserver"}
    # International name search needs no access code or provider configuration.
    blocked = client.post("/api/product-search",json={"query":"洗衣粉"},
                          headers={"origin":"https://example.invalid"})
    assert blocked.status_code == 403
    assert client.post("/api/product-search",
                       json={"query":"洗衣粉","photo":"private image"},
                       headers=origin).status_code == 422
    assert not calls, "No external calls without same-origin valid request"
    r=client.post("/api/product-search",json={"query":"洗衣粉"},headers=origin)
    assert r.status_code == 200,r.text
    rows=r.json()["results"]
    assert len(rows)==2
    assert rows[0]["name"]=="洗衣粉"
    assert rows[0]["source"]=="Open Products Facts"
    assert any(x["source"]=="Open Beauty Facts" for x in rows)
    assert all(x["recommendation_permission"] is False for x in rows)
    assert all(x["review_status"]=="unreviewed" for x in rows)
    assert all("unsafe_instructions" not in str(x) for x in rows)
    assert len(calls)==len(PLATFORMS)
    # Repeated searches hit the bounded memory cache.
    assert client.post("/api/product-search",json={"query":"洗衣粉"},
                       headers=origin).status_code==200
    assert len(calls)==len(PLATFORMS)
    print("GQ_GLOBAL_NAME_SEARCH_SMOKE_PASS")

    result=client.post("/api/product-lookup",
                       json={"barcode":GOOD},headers=origin)
    assert result.status_code==200,result.text
    candidate=result.json()
    assert candidate["found"] is True
    assert candidate["name"]=="World Cleanser"
    assert candidate["category"]=="beauty"
    assert candidate["source"]=="Open Beauty Facts"
    assert candidate["recommendation_permission"] is False
    assert len(calls)==len(PLATFORMS)+len(PLATFORMS)
    print("GQ_GLOBAL_CROSS_CATEGORY_BARCODE_SMOKE_PASS")

print("GQ_GLOBAL_NO_PHOTOS_NO_PAID_PROVIDER_SMOKE_PASS")
