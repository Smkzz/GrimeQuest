"""Local-only product OCR: strict consent, private images, resource limits and provenance."""
import base64
import importlib
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from server.models import ProductObservation
from server.config import Settings
from server import ocr
from conftest import make_image


def test_ocr_recognizes_two_labels_without_external_calls_or_files(monkeypatch):
    seen=[]
    text_outputs=["KIILTO KOTI\nYleispuhdistussuihke", "KÄYTTÖOHJE\nLue ohjeet ja varoitukset"]
    def fake_run(argv, **kw):
        assert argv==["tesseract","stdin","stdout","-l","fin+eng","--psm","6"]
        assert isinstance(kw["input"],bytes) and kw["input"][:3]==b"\xff\xd8\xff"
        assert "GQ_PROVIDER_KEY" not in kw["env"]
        assert kw["timeout"]==12 and kw["check"] is False
        seen.append(argv)
        return SimpleNamespace(returncode=0,stdout=text_outputs[len(seen)-1].encode())
    monkeypatch.setattr(ocr,"available",lambda:True)
    monkeypatch.setattr(ocr.subprocess,"run",fake_run)
    photo=make_image(size=(320,240))
    obs=ocr.recognize_product(photo,photo)
    assert len(seen)==2
    assert obs.name=="KIILTO KOTI"
    assert obs.label_readable
    assert "KÄYTTÖOHJE" in obs.label_text
    assert obs.warnings_observed==[]
    assert "UNVERIFIED" in obs.label_text


def test_ocr_unreadable_directions_never_claim_complete_label(monkeypatch):
    outputs=["KIILTO KOTI",""]
    monkeypatch.setattr(ocr,"available",lambda:True)
    monkeypatch.setattr(ocr.subprocess,"run",lambda *args,**kw: SimpleNamespace(returncode=0,stdout=outputs.pop(0).encode()))
    data=make_image()
    result=ocr.recognize_product(data,data)
    assert result.label_readable is False
    assert "[No text recognized]" in result.label_text


def test_no_external_provider_request_and_no_private_code_needed_for_ocr(monkeypatch):
    m=importlib.import_module("server.app")
    invoked=[]
    monkeypatch.setattr(m,"ocr_available",lambda:True)
    def fake_ocr(front,back):
        invoked.append((front,back))
        return ProductObservation(name="Kiilto Koti",label_readable=True,label_text="UNVERIFIED\nLue käyttöohje",warnings_observed=[])
    monkeypatch.setattr(m,"recognize_product",fake_ocr)
    with TestClient(m.create_app(Settings())) as client:
        health=client.get("/api/health").json()
        assert health["live_ready"] is False
        assert health["label_ocr_ready"] is True
        photo=make_image()
        body={"front_image":photo,"back_image":photo,"consent":True}
        headers={"origin":"http://testserver"}
        response=client.post("/api/read-labels",json=body,headers=headers)
        assert response.status_code==200,response.text
        payload=response.json()
        assert payload["extraction"]=="server_local_tesseract"
        assert payload["recommendation_permission"] is False
        assert payload["review_status"]=="unreviewed"
        assert payload["provider_calls"]==0
        assert payload["observation"]["name"]=="Kiilto Koti"
        assert "data:image" not in response.text
        assert len(invoked)==1


def test_ocr_uses_same_origin_explicit_consent_and_size_rules(monkeypatch):
    m=importlib.import_module("server.app")
    monkeypatch.setattr(m,"ocr_available",lambda:True)
    monkeypatch.setattr(m,"recognize_product",lambda a,b:pytest.fail("Must reject before calling OCR"))
    with TestClient(m.create_app(Settings())) as client:
        photo=make_image()
        body={"front_image":photo,"back_image":photo,"consent":True}
        assert client.post("/api/read-labels",json=body,headers={"origin":"https://evil.example"}).status_code==403
        assert client.post("/api/read-labels",json={**body,"consent":False},headers={"origin":"http://testserver"}).status_code==422
        assert client.post("/api/read-labels",json={**body,"front_image":"x"},headers={"origin":"http://testserver"}).status_code==422
        assert client.post("/api/read-labels",data=b"x"*5_700_001,headers={"origin":"http://testserver","content-type":"application/json"}).status_code==413


def test_ocr_budget_is_separate_and_stops_excess_requests(monkeypatch):
    m=importlib.import_module("server.app")
    monkeypatch.setattr(m,"ocr_available",lambda:True)
    monkeypatch.setattr(m,"recognize_product",lambda a,b:pytest.fail("OCR quota must block first"))
    with TestClient(m.create_app(Settings())) as client:
        import time
        client.app.state.ocr_calls.extend([time.monotonic()]*36)
        body={"front_image":make_image(),"back_image":make_image(),"consent":True}
        response=client.post("/api/read-labels",json=body,headers={"origin":"http://testserver"})
        assert response.status_code==429
        assert "busy" in response.text.lower()


def test_ocr_unavailable_fails_without_images_or_provider_call(monkeypatch):
    m=importlib.import_module("server.app")
    monkeypatch.setattr(m,"ocr_available",lambda:False)
    with TestClient(m.create_app(Settings())) as client:
        health=client.get("/api/health").json()
        assert health["label_ocr_ready"] is False
        response=client.post("/api/read-labels",
            json={"front_image":make_image(),"back_image":make_image(),"consent":True},
            headers={"origin":"http://testserver"})
        assert response.status_code==503
        assert "data:image" not in response.text
