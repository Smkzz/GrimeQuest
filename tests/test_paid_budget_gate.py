"""A provider limit must be verified *before* the evaluator makes any model call."""
import asyncio
from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from PIL import Image
from server.provider import ProviderFailure
from scripts import evaluate_provider as cli


def args(manifest: Path, output: Path):
    return SimpleNamespace(
        manifest=str(manifest), output=str(output), max_cases=0,
        allow_small=False, delay_ms=0, timeout=10.0,
    )


def manifest(tmp_path: Path):
    path=tmp_path / "manifest.json"
    path.write_text(json.dumps({"version":1,"cases":[
        {"id":"unsupported-1","task":"target","image":"test.jpg",
         "truth":{"supported":False}}
    ]}),encoding="utf-8")
    return path


def test_oversized_provider_cap_prevents_all_inference(monkeypatch,tmp_path):
    m=manifest(tmp_path)
    monkeypatch.setenv("GQ_PROVIDER_BASE","https://openrouter.ai/api/v1")
    monkeypatch.setenv("GQ_PROVIDER_MODEL","google/gemini-2.5-flash-lite")
    monkeypatch.setenv("GQ_PROVIDER_KEY","synthetic-key-no-network")
    calls=[]

    async def reject_budget(key,maximum_usd):
        calls.append(("budget",maximum_usd))
        raise ProviderFailure("Oversized provider-side limit")

    monkeypatch.setattr(cli,"verify_openrouter_key_limit",reject_budget)
    monkeypatch.setattr(cli,"VisionProvider",lambda *a,**kw: pytest.fail("model initialized before cap verification"))
    with pytest.raises(SystemExit,match="No paid request was made"):
        asyncio.run(cli.main_async(args(m,tmp_path/"result.json")))
    assert calls==[("budget",0.50)]
    assert not (tmp_path/"result.json").exists()


def test_variable_router_and_unknown_billing_host_are_rejected(monkeypatch,tmp_path):
    m=manifest(tmp_path)
    monkeypatch.setenv("GQ_PROVIDER_BASE","https://openrouter.ai/api/v1")
    monkeypatch.setenv("GQ_PROVIDER_KEY","synthetic-key")
    monkeypatch.setenv("GQ_PROVIDER_MODEL","openrouter/free")
    with pytest.raises(SystemExit,match="fixed model"):
        asyncio.run(cli.main_async(args(m,tmp_path/"result.json")))
    monkeypatch.setenv("GQ_PROVIDER_BASE","https://unverified-provider.example/v1")
    monkeypatch.setenv("GQ_PROVIDER_MODEL","paid-model")
    with pytest.raises(SystemExit,match="verified OpenRouter billing API"):
        asyncio.run(cli.main_async(args(m,tmp_path/"result.json")))


def test_cap_verification_precedes_first_model_observation(monkeypatch,tmp_path):
    m=manifest(tmp_path)
    Image.new("RGB",(96,96),"white").save(tmp_path/"test.jpg")
    monkeypatch.setenv("GQ_PROVIDER_BASE","https://openrouter.ai/api/v1")
    monkeypatch.setenv("GQ_PROVIDER_MODEL","google/gemini-2.5-flash-lite")
    monkeypatch.setenv("GQ_PROVIDER_KEY","synthetic-key-no-network")
    events=[]

    async def accept_budget(key,maximum_usd):
        assert maximum_usd==0.50
        events.append("verified_cap")
        return {"verified":True,"limit_usd":0.50,"remaining_usd":0.50,"reset":None}

    class FakeProvider:
        def __init__(self,*a,**kw):
            events.append("model_initialized")
        async def analyze(self,image):
            events.append("model_called")
            from server.models import TargetAnalysis
            return TargetAnalysis(
                object_name="unidentified test surface",surface="unknown",soil="unknown",
                visible_soil=False,image_quality="usable",material_certainty="unknown",
                hazards=["none"],target_box={"x":0.0,"y":0.0,"width":1.0,"height":1.0},
            )

    monkeypatch.setattr(cli,"verify_openrouter_key_limit",accept_budget)
    monkeypatch.setattr(cli,"VisionProvider",FakeProvider)
    outfile=tmp_path/"out"/"eval.json"
    status=asyncio.run(cli.main_async(args(m,outfile)))
    assert status==2  # Dataset minimums were not met; no release qualification.
    assert events==["verified_cap","model_initialized","model_called"]
    payload=json.loads(outfile.read_text(encoding="utf-8"))
    assert payload["provider_key_limit_verified"]["limit_usd"]==0.50
    assert payload["routing_policy"]=={"zdr":True,"data_collection":"deny","require_parameters":True}
    assert payload["summary"]["qualified"] is False
