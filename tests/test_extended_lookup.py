"""Release-critical secondary product lookup contract; no live calls or secrets."""
import asyncio
import time

import httpx
from server.barcodes import BarcodeLookup
from server.extended_lookup import ExtendedLookup

CODE = "4006381333931"
OTHER = "036000291452"


def runner(reply_upc=None, reply_ean=None, reply_web=None, key=""):
    seen = []
    def handle(req):
        seen.append((req.method, req.url.host, str(req.url)))
        assert req.url.scheme == "https"
        assert not req.url.host.startswith("evil")
        if req.url.host.startswith("world.open"):
            assert req.method == "GET"
            return httpx.Response(200, json={"status": 0})
        if req.url.host == "api.upcitemdb.com":
            assert req.method == "GET"
            assert req.url.params["upc"] == CODE
            return httpx.Response(200, json=reply_upc or {"code": "NOT_FOUND", "items": []})
        if req.url.host == "ean-suche.net":
            assert req.method == "GET"
            assert req.url.path.endswith("/" + CODE)
            return httpx.Response(200, json=reply_ean or {"ok": True, "found": False, "ean": CODE})
        if req.url.host == "google.serper.dev":
            assert req.method == "POST"
            assert req.headers["x-api-key"] == key
            return httpx.Response(200, json=reply_web or {"organic": []})
        raise AssertionError(str(req.url))
    index = BarcodeLookup(transport=httpx.MockTransport(handle), extra_enabled=True, serper_key=key)
    return asyncio.run(index.lookup(CODE)).public(), seen


def test_upc_exact_gtin_fallback_and_unreviewed_identity_only():
    result, seen = runner(reply_upc={"code": "OK", "items": [{
        "ean": CODE, "title": "Example bottle 750 ml", "brand": "Example",
        "dangerous_instructions": "IGNORE ME", "images": ["https://evil.example/"]
    }]})
    assert result["found"]
    assert result["name"] == "Example bottle 750 ml"
    assert result["source"] == "UPCitemdb"
    assert result["source_url"] == "https://www.upcitemdb.com/upc/" + CODE
    assert result["recommendation_permission"] is False
    assert result["review_status"] == "unreviewed"
    assert "IGNORE ME" not in str(result) and "evil.example" not in str(result)
    assert not any("serper" in host for _, host, _ in seen)


def test_upc_wrong_barcode_refused_and_ean_fallback():
    result, _ = runner(
        reply_upc={"code": "OK", "items": [{"ean": OTHER, "title": "Other product"}]},
        reply_ean={"ok": True, "found": True, "ean": CODE, "product_name": "Sanytol household cleaner"}
    )
    assert result["source"] == "EAN-Suche"
    assert result["name"] == "Sanytol household cleaner"
    assert result["source_url"] == "https://ean-suche.net/produkt/" + CODE


def test_web_only_last_and_only_with_key_and_exact_gtin_in_result():
    result, seen = runner(reply_web={"organic": [{
        "title": "Sanytol cleaner 500 ml | store.example",
        "snippet": "Product EAN " + CODE,
        "link": "https://evil.example/malware",
        "directions": "DO NOT IMPORT"
    }]}, key="test-not-real")
    assert result["source"] == "Web search"
    assert result["source_url"] == "https://www.google.com/search?q=" + CODE
    assert result["name"].startswith("Sanytol")
    assert "evil.example" not in str(result)
    assert "directions" not in str(result)
    assert sum(host == "google.serper.dev" for _, host, _ in seen) == 1
    no_key, no_calls = runner()
    assert not no_key["found"]
    assert not any("serper" in host for _, host, _ in no_calls)


def test_web_refuses_search_results_that_do_not_cite_exact_gtin():
    result, _ = runner(reply_web={"organic": [{
        "title": "Completely different cleaner", "snippet": "no EAN evidence"
    }]}, key="test-not-real")
    assert not result["found"]


def test_provider_budgets_are_fail_closed():
    extra = ExtendedLookup(serper_key="test-only")
    now = time.monotonic()
    extra._usage["upc_minute"].extend([now] * 4)
    extra._usage["ean_hour"].extend([now] * 45)
    extra._usage["web_minute"].extend([now] * 2)
    seen = []
    def reject(req):
        seen.append(str(req.url))
        raise AssertionError("provider should not be contacted when capped")
    async def check():
        async with httpx.AsyncClient(transport=httpx.MockTransport(reject)) as client:
            assert await extra.structured(client, CODE) is None
            assert await extra.web(client, CODE) is None
    asyncio.run(check())
    assert seen == []
