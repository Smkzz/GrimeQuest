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


def _tsv(lines, confidence=96):
    """Tiny deterministic stand-in for Tesseract's actual TSV word output."""
    rows=["level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext"]
    for i,line in enumerate(lines,1):
        for j,word in enumerate(line.split(),1):
            rows.append(f"5\t1\t1\t1\t{i}\t{j}\t{j*80}\t{i*60}\t60\t40\t{confidence}\t{word}")
    return ("\n".join(rows)+"\n").encode("utf-8")


def test_ocr_recognizes_two_labels_without_external_calls_or_files(monkeypatch):
    seen=[]
    results=[
        _tsv(["KIILTO KOTI","Yleispuhdistussuihke"]),
        _tsv(["KÄYTTÖOHJE","Lue ohjeet ja varoitukset"])
    ]
    def fake_run(argv, **kw):
        assert argv==["tesseract","stdin","stdout","-l","fin+eng","--psm","11","tsv"]
        assert isinstance(kw["input"],bytes) and kw["input"][:3]==b"\xff\xd8\xff"
        assert "GQ_PROVIDER_KEY" not in kw["env"]
        assert kw["timeout"]==6.5 and kw["check"] is False
        seen.append(argv)
        return SimpleNamespace(returncode=0,stdout=results.pop(0))
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
    outputs=[_tsv(["KIILTO KOTI"]),_tsv(["KIILTO KOTI"]),_tsv([]),_tsv([])]
    monkeypatch.setattr(ocr,"available",lambda:True)
    monkeypatch.setattr(ocr.subprocess,"run",lambda *args,**kw: SimpleNamespace(returncode=0,stdout=outputs.pop(0)))
    data=make_image()
    result=ocr.recognize_product(data,data)
    assert result.label_readable is False
    assert "[No reliable text recognized]" in result.label_text
    assert "OCR QUALITY WARNING" in result.label_text


def test_ocr_rejects_screenshot_like_noise_as_a_product_name(monkeypatch):
    """Regression: '| MTT' and 'LSANYTOL | VS' from the real iPhone screenshot."""
    outputs=[
        _tsv(["| MTT","< - M","LSANYTOL | VS"],confidence=90),
        _tsv(["| MTT","< - M","LSANYTOL | VS"],confidence=90),
        _tsv(["DIRECTIONS WARNINGS","Read instructions before use"],confidence=94)
    ]
    monkeypatch.setattr(ocr,"available",lambda:True)
    monkeypatch.setattr(ocr.subprocess,"run",lambda *a,**kw:SimpleNamespace(returncode=0,stdout=outputs.pop(0)))
    img=make_image()
    observation=ocr.recognize_product(img,img)
    assert observation.name==ocr.NAME_UNREADABLE
    assert observation.label_readable is False
    assert "OCR QUALITY WARNING" in observation.label_text


def test_ocr_rejects_low_confidence_two_word_name_even_if_readable_shape(monkeypatch):
    outputs=[_tsv(["FAKE CLEANER"],confidence=39)]*4
    monkeypatch.setattr(ocr,"available",lambda:True)
    monkeypatch.setattr(ocr.subprocess,"run",lambda *a,**kw:SimpleNamespace(returncode=0,stdout=outputs.pop(0)))
    img=make_image()
    result=ocr.recognize_product(img,img)
    assert result.name==ocr.NAME_UNREADABLE
    assert result.label_readable is False


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
