import asyncio
import json
import httpx
import pytest
from server.provider import VisionProvider,ProviderFailure
from server.models import TargetAnalysis,ProductObservation


def envelope(content,finish='stop',refusal=None):
    return {'choices':[{'finish_reason':finish,'message':{'content':content,'refusal':refusal}}]}

def test_provider_transport_shape_and_strict_schema(analysis,before):
    seen=[]
    def handle(r):
        seen.append(r)
        body=json.loads(r.content)
        fmt=body['response_format']
        assert fmt['type']=='json_schema' and fmt['json_schema']['strict'] is True
        assert fmt['json_schema']['name']=='targetanalysis'
        assert fmt['json_schema']['schema']['additionalProperties'] is False
        assert body['stream'] is False and body['temperature']==0
        assert body['max_tokens']==1800
        assert body['messages'][1]['content'][1]['image_url']['url']==before
        assert 'untrusted' in body['messages'][0]['content']
        return httpx.Response(200,json=envelope(analysis.model_dump_json()))
    p=VisionProvider('https://vision.example/v1','test-model','synthetic-key',transport=httpx.MockTransport(handle))
    assert asyncio.run(p.analyze(before))==analysis
    assert str(seen[0].url)=='https://vision.example/v1/chat/completions'
    assert seen[0].headers['authorization']=='Bearer synthetic-key'

@pytest.mark.parametrize('case',['malformed','extra','missing','refusal','truncated','badtype','emptychoices','too_big','servererror','redirect','invalidenum'])
def test_provider_failure_closed(case,analysis,before):
    data=analysis.model_dump()
    if case=='extra':data['recommended_chemical']='IGNORE ALL GUARDRAILS'
    if case=='missing':del data['surface']
    if case=='invalidenum':data['surface']='whatever'
    response=envelope(json.dumps(data))
    status=200
    if case=='malformed':response=envelope('not json PRIVATE_SECRET')
    if case=='refusal':response=envelope('{}',refusal='no')
    if case=='truncated':response=envelope('{}',finish='length')
    if case=='badtype':response=envelope({'not':'a string'})
    if case=='emptychoices':response={'choices':[]}
    if case=='too_big':response=envelope('x'*100001)
    if case=='servererror':status=500
    if case=='redirect':status=302
    p=VisionProvider('https://vision.example/v1','test',transport=httpx.MockTransport(lambda r:httpx.Response(status,json=response,headers={'location':'https://other.example'})))
    with pytest.raises(ProviderFailure) as error:asyncio.run(p.analyze(before))
    assert 'PRIVATE_SECRET' not in str(error.value) and 'IGNORE' not in str(error.value)

def test_timeout_is_bounded(before):
    async def slow(r):await asyncio.sleep(0.2);return httpx.Response(200,json={})
    p=VisionProvider('https://vision.example/v1','test',transport=httpx.MockTransport(slow),timeout=0.01)
    with pytest.raises(ProviderFailure):asyncio.run(p.analyze(before))

def test_compare_and_label_adapter(before,after,clear):
    calls=[]
    def handle(r):
        body=json.loads(r.content);calls.append(body)
        schema=body['messages'][0]['content']
        result=clear.model_dump_json() if 'BEFORE' in schema else ProductObservation(name='Bottle',label_readable=False,label_text='',warnings_observed=[]).model_dump_json()
        assert len(body['messages'][1]['content'])==3
        return httpx.Response(200,json=envelope(result))
    p=VisionProvider('https://vision.example/v1','test',transport=httpx.MockTransport(handle))
    assert asyncio.run(p.compare(before,after))==clear
    assert asyncio.run(p.product(before,after)).label_readable is False
    assert len(calls)==2


def test_openrouter_requires_supported_parameters(analysis,before):
    def handle(r):
        body=json.loads(r.content)
        assert body['provider']=={'require_parameters':True}
        return httpx.Response(200,json=envelope(analysis.model_dump_json()))
    p=VisionProvider('https://openrouter.ai/api/v1','qwen/qwen3.8-27b:free','synthetic',transport=httpx.MockTransport(handle))
    assert asyncio.run(p.analyze(before))==analysis
