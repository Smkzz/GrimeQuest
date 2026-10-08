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
