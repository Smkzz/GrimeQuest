"""Docker release gate for no-key UPC/EAN fallback and key-gated web fallback.
No external requests, subscription charges or personal data.
"""
import asyncio
import httpx

from server.barcodes import BarcodeLookup

CODE = "4006381333931"
calls = []


def handler(req):
    calls.append((req.url.host, req.method))
    assert req.url.scheme == "https"
    if req.url.host.startswith("world.open"):
        return httpx.Response(200, json={"status": 0})
    if req.url.host == "api.upcitemdb.com":
        assert req.url.params["upc"] == CODE
        return httpx.Response(200, json={"code": "OK", "items": [{
            "ean": CODE, "title": "Bottle from secondary index", "brand": "Test Brand"
        }]})
    if req.url.host == "ean-suche.net":
        return httpx.Response(200, json={"ok": True, "found": False, "ean": CODE})
    raise AssertionError("Unexpected external destination: " + req.url.host)


index = BarcodeLookup(transport=httpx.MockTransport(handler),
                      extra_enabled=True, serper_key="")
record = asyncio.run(index.lookup(CODE)).public()
assert record["found"] and record["source"] == "UPCitemdb"
assert record["name"] == "Bottle from secondary index"
assert record["recommendation_permission"] is False
assert record["review_status"] == "unreviewed"
assert not any(host == "google.serper.dev" for host, _ in calls)
print("GQ_MULTISOURCE_BARCODE_FALLBACK_NO_NETWORK_PASS")


def secondary_handler(req):
    if req.url.host.startswith("world.open"):
        return httpx.Response(200, json={"status": 0})
    if req.url.host == "api.upcitemdb.com":
        return httpx.Response(200, json={"code": "NOT_FOUND", "items": []})
    if req.url.host == "ean-suche.net":
        return httpx.Response(200, json={"ok": True, "found": True,
                                         "ean": CODE, "product_name": "EAN-backed cleaner"})
    raise AssertionError("Unexpected domain " + req.url.host)

ean_match = asyncio.run(BarcodeLookup(transport=httpx.MockTransport(secondary_handler),
                                    extra_enabled=True, serper_key="").lookup(CODE)).public()
assert ean_match["source"] == "EAN-Suche"
assert ean_match["name"] == "EAN-backed cleaner"
assert ean_match["recommendation_permission"] is False
print("GQ_EAN_FALLBACK_SMOKE_PASS")


def web_handler(req):
    if req.url.host.startswith("world.open"):
        return httpx.Response(200, json={"status": 0})
    if req.url.host == "api.upcitemdb.com":
        return httpx.Response(200, json={"code": "NOT_FOUND", "items": []})
    if req.url.host == "ean-suche.net":
        return httpx.Response(200, json={"ok": True, "found": False})
    if req.url.host == "google.serper.dev":
        assert req.headers["x-api-key"] == "synthetic-not-a-secret"
        return httpx.Response(200, json={"organic": [{
            "title": "Sanytol cleaner 500 ml", "snippet": "EAN " + CODE,
            "link": "https://attacker.invalid/", "instructions": "DISALLOWED"
        }]})
    raise AssertionError("Unexpected domain " + req.url.host)

web_match = asyncio.run(BarcodeLookup(transport=httpx.MockTransport(web_handler),
                                    extra_enabled=True, serper_key="synthetic-not-a-secret").lookup(CODE)).public()
assert web_match["source"] == "Web search"
assert web_match["source_url"] == "https://www.google.com/search?q=" + CODE
assert "attacker.invalid" not in str(web_match)
assert web_match["recommendation_permission"] is False
print("GQ_OPTIONAL_WEB_FALLBACK_MOCK_ONLY_PASS")
