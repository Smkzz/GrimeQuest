import pytest
from server.models import Comparison
from server.policy import CATALOG
from server.provider import ProviderFailure
from conftest import start_encounter,verify,HEADERS,PRODUCT,make_image

def test_full_workflow_and_idempotent_xp(client,vision,before,after,attestations):
    encounter=start_encounter(client,before,attestations)
    r=verify(client,encounter,before,after)
    assert r.status_code==200,r.text
    result=r.json()
    assert result['status']=='clear' and result['xp']==300 and result['receipt']
    assert result['provenance']=='model_observation'
    assert verify(client,encounter,before,after).json()==result
    assert verify(client,encounter,before,make_image('ivory')).json()==result
    assert vision.calls==['analyze','compare']

def test_before_binding_and_identical_guard(client,vision,before,after,attestations):
    encounter=start_encounter(client,before,attestations)
    r=verify(client,encounter,make_image('blue'),after)
    assert r.status_code==409
    r=verify(client,encounter,before,before)
    assert r.json()['status']=='unverifiable' and r.json()['xp']==0
    assert r.json()['provenance']=='deterministic_guard'
    assert vision.calls==['analyze']

@pytest.mark.parametrize('field',['consent','procedure_completed','surface_dry'])
def test_verification_requires_attestation(client,vision,before,after,attestations,field):
    encounter=start_encounter(client,before,attestations)
    assert verify(client,encounter,before,after,**{field:False}).status_code==422
    assert vision.calls==['analyze']

def test_unsigned_or_wrong_purpose_cannot_skip_workflow(client,vision,before,after,attestations):
    r=client.post('/api/start',headers=HEADERS,json={'target_ticket':'forged.'+'0'*64,'surface':'glazed_ceramic','soil':'grease','product_id':PRODUCT,'attestations':attestations.model_dump()})
    assert r.status_code==409 and not vision.calls
    r=client.post('/api/analyze-target',headers=HEADERS,json={'image':before,'consent':True})
    target=r.json()['target_ticket']
    assert verify(client,{'encounter_ticket':target},before,after).status_code==409

@pytest.mark.parametrize('patch',[{'hazards':['heat']},{'visible_soil':False},{'image_quality':'unusable'}])
def test_signed_observation_restrictions_cannot_be_overridden(client,vision,before,attestations,patch):
    vision.analysis=type(vision.analysis)(**{**vision.analysis.model_dump(),**patch})
    r=client.post('/api/analyze-target',headers=HEADERS,json={'image':before,'consent':True})
    r=client.post('/api/start',headers=HEADERS,json={'target_ticket':r.json()['target_ticket'],'surface':'glazed_ceramic','soil':'grease','product_id':PRODUCT,'attestations':attestations.model_dump()})
    assert r.status_code==409
    assert vision.calls==['analyze']

def test_model_failure_does_not_complete_or_leak(client,vision,before,after,attestations):
    encounter=start_encounter(client,before,attestations)
    vision.failure=ProviderFailure('Vision unavailable. No result was awarded.')
    r=verify(client,encounter,before,after)
    assert r.status_code==502 and 'receipt' not in r.json() and 'xp' not in r.json()
    vision.failure=None
    assert verify(client,encounter,before,after).json()['status']=='clear'

def test_partial_cached_then_clear(client,vision,before,after,attestations):
    encounter=start_encounter(client,before,attestations)
    vision.comparison=Comparison(**{**vision.comparison.model_dump(),'residue_after':'reduced','improvement':'some'})
    r=verify(client,encounter,before,after)
    assert r.json()['status']=='partial' and r.json()['xp']==0
    assert verify(client,encounter,before,after).json()==r.json()
    vision.comparison=Comparison(**{**vision.comparison.model_dump(),'residue_after':'not_visible','improvement':'substantial'})
    assert verify(client,encounter,before,make_image('ivory')).json()['status']=='clear'
    assert vision.calls==['analyze','compare','compare']

def test_catalog_changed_invalidates_receipt(client,before,after,attestations,monkeypatch):
    encounter=start_encounter(client,before,attestations)
    monkeypatch.setitem(CATALOG,'version','replacement')
    assert verify(client,encounter,before,after).status_code==409

def test_label_scan_never_grants_recommendation(client,vision,before,after):
    r=client.post('/api/analyze-product',headers=HEADERS,json={'front_image':before,'back_image':after,'consent':True})
    assert r.status_code==200 and r.json()['review_status']=='unreviewed'
    assert r.json()['recommendation_permission'] is False
    assert 'surfaces' not in r.json()['observation']

def test_matching_api_and_health_do_not_leak_key(client,attestations):
    r=client.post('/api/match',headers=HEADERS,json={'surface':'glazed_ceramic','soil':'grease','product_id':PRODUCT,'attestations':attestations.model_dump(),'hazards':['none']})
    assert r.json()['status']=='eligible'
    h=client.get('/api/health');assert h.json()['live_ready'] is True;assert h.json()['workflow_receipts_persistent'] is True
    assert 'fake-secret' not in h.text and 'test-only-access' not in h.text

def test_concurrent_verification_is_single_flight(settings,analysis,clear,before,after,attestations):
    import asyncio
    import httpx
    from server.app import create_app
    from conftest import FakeVision
    async def run():
        started=asyncio.Event();release=asyncio.Event()
        class SlowVision(FakeVision):
            async def compare(self,b,a):
                self.check('compare');started.set();await release.wait();return self.comparison
        vision=SlowVision(analysis,clear);app=create_app(settings,vision)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://testserver',headers=HEADERS) as c:
            a=await c.post('/api/analyze-target',json={'image':before,'consent':True})
            s=await c.post('/api/start',json={'target_ticket':a.json()['target_ticket'],'surface':'glazed_ceramic','soil':'grease','product_id':PRODUCT,'attestations':attestations.model_dump()})
            payload={'encounter_ticket':s.json()['encounter_ticket'],'before_image':before,'after_image':after,'consent':True,'procedure_completed':True,'surface_dry':True}
            first=asyncio.create_task(c.post('/api/verify',json=payload));await asyncio.wait_for(started.wait(),2)
            second=await c.post('/api/verify',json=payload);assert second.status_code==409
            release.set();assert (await first).json()['status']=='clear'
            assert vision.calls==['analyze','compare'] and app.state.budget.active==0
    asyncio.run(run())


def test_workflow_ticket_survives_restart_with_configured_secret(settings,analysis,clear,before,attestations):
    from fastapi.testclient import TestClient
    from server.app import create_app
    from conftest import FakeVision
    first_vision=FakeVision(analysis,clear)
    with TestClient(create_app(settings,first_vision)) as first:
        target=first.post('/api/analyze-target',headers=HEADERS,json={'image':before,'consent':True}).json()['target_ticket']
    second_vision=FakeVision(analysis,clear)
    with TestClient(create_app(settings,second_vision)) as second:
        r=second.post('/api/start',headers=HEADERS,json={'target_ticket':target,'surface':'glazed_ceramic','soil':'grease','product_id':PRODUCT,'attestations':attestations.model_dump()})
        assert r.status_code==200,r.text
        assert r.json()['encounter_ticket']
