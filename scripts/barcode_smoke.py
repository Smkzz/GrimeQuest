"""No-network smoke: strict barcode validation, optional community lookup, no photos."""
from fastapi.testclient import TestClient
import httpx
from server.barcodes import BarcodeLookup, valid_gtin
from server.app import create_app
from server.config import Settings

EAN = "4006381333931"
assert valid_gtin(EAN) and not valid_gtin("4006381333932")
calls = []


def index(request):
    calls.append(request)
    assert request.method == "GET"
    assert request.url.host == "world.openproductsfacts.org"
    assert request.url.path == "/api/v2/product/" + EAN + ".json"
    assert request.headers["user-agent"].startswith("GrimeQuest/")
    assert request.content == b""
    return httpx.Response(200, json={"status": 1, "code": EAN, "product": {
        "product_name_fi": "Kiilto Koti", "brands": "Kiilto",
        "quantity": "600 ml", "dangerous_advice": "do not import"
    }})


app = create_app(Settings(), barcode_lookup=BarcodeLookup(
    transport=httpx.MockTransport(index)
))
with TestClient(app) as client:
    origin = {"origin": "http://testserver"}
    assert client.post("/api/product-lookup", json={"barcode": EAN},
                       headers={"origin": "https://attacker.example"}).status_code == 403
    assert client.post("/api/product-lookup", json={"barcode": "4006381333932"},
                       headers=origin).status_code == 422
    assert not calls
    r = client.post("/api/product-lookup", json={"barcode": EAN}, headers=origin)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["found"] and data["name"] == "Kiilto Koti"
    assert data["recommendation_permission"] is False
    assert data["review_status"] == "unreviewed"
    assert "dangerous_advice" not in r.text
    assert "data:image" not in r.text
    assert len(calls) == 1
    assert client.post("/api/product-lookup",
                       json={"barcode": EAN}, headers=origin).status_code == 200
    assert len(calls) == 1, "Safe cache must prevent duplicate upstream request"
    print("GQ_BARCODE_LOOKUP_SMOKE_PASS")

with TestClient(create_app(Settings(), barcode_lookup=BarcodeLookup(
        transport=httpx.MockTransport(lambda _: httpx.Response(
            200, json={"status": 0})))))) as client:
    fallback = client.post("/api/product-lookup",
                           json={"barcode": EAN},
                           headers={"origin": "http://testserver"})
    assert fallback.status_code == 200
    assert not fallback.json()["found"]
    assert fallback.json()["name"] == ""
    assert fallback.json()["recommendation_permission"] is False
    print("GQ_BARCODE_UNKNOWN_MANUAL_FALLBACK_PASS")
