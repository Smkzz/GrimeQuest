import asyncio
import json
import httpx
import pytest
from server.provider import VisionProvider,ProviderFailure,validate_openrouter_key_limit,verify_openrouter_key_limit,verify_openrouter_zdr_model
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
        assert body['provider']=={'require_parameters':True,'zdr':True,'data_collection':'deny'}
        return httpx.Response(200,json=envelope(analysis.model_dump_json()))
    p=VisionProvider('https://openrouter.ai/api/v1','qwen/qwen3.8-27b:free','synthetic',transport=httpx.MockTransport(handle))
    assert asyncio.run(p.analyze(before))==analysis


def test_key_budget_requires_a_small_nonresetting_provider_limit():
    accepted={'limit':0.50,'limit_remaining':0.49,'limit_reset':None,'is_management_key':False,'include_byok_in_limit':True}
    assert validate_openrouter_key_limit(accepted)['verified'] is True
    assert validate_openrouter_key_limit({**accepted,'limit':0.25,'limit_remaining':0.1})['limit_usd']==0.25
    for patch in [
        {'limit':10.0,'limit_remaining':6.0},
        {'limit':None},
        {'limit':'0.50'},
        {'limit':0.0,'limit_remaining':0.0},
        {'limit':0.50,'limit_remaining':0.51},
        {'limit':0.50,'limit_remaining':-0.01},
        {'limit':0.50,'limit_reset':'daily'},
        {'limit':0.50,'limit_reset':'monthly'},
        {'limit':0.50,'is_management_key':True},
        {'limit':0.50,'include_byok_in_limit':False},
    ]:
        with pytest.raises(ProviderFailure):
            validate_openrouter_key_limit({**accepted,**patch})
    with pytest.raises(ProviderFailure):
        validate_openrouter_key_limit({k:v for k,v in accepted.items() if k!='limit_reset'})
    with pytest.raises(ProviderFailure):
        validate_openrouter_key_limit({k:v for k,v in accepted.items() if k!='include_byok_in_limit'})
    with pytest.raises(ProviderFailure):
        validate_openrouter_key_limit(None)


def test_openrouter_budget_preflight_is_read_only_and_fails_closed():
    calls=[]
    def handle(request):
        calls.append((request.method, str(request.url)))
        assert request.method=='GET' and str(request.url)=='https://openrouter.ai/api/v1/key'
        assert request.headers['authorization']=='Bearer only-in-memory-test-key'
        return httpx.Response(200,json={'data':{'limit':0.50,'limit_remaining':0.49,'limit_reset':None,'is_management_key':False,'include_byok_in_limit':True}})
    verified=asyncio.run(verify_openrouter_key_limit(
        'only-in-memory-test-key',transport=httpx.MockTransport(handle)))
    assert verified['limit_usd']==0.50 and len(calls)==1

    for response in [httpx.Response(403,json={'error':'denied'}),
                     httpx.Response(200,json={'data':{'limit':10,'limit_remaining':9,'limit_reset':None}}),
                     httpx.Response(200,text='not json')]:
        with pytest.raises(ProviderFailure):
            asyncio.run(verify_openrouter_key_limit(
                'only-in-memory-test-key',
                transport=httpx.MockTransport(lambda request, response=response:response)))
    with pytest.raises(ProviderFailure):
        asyncio.run(verify_openrouter_key_limit('only-in-memory-test-key',maximum_usd=1))


def test_zdr_preflight_requires_fixed_model_and_supported_parameters():
    calls=[]
    def handle(request):
        calls.append((request.method,str(request.url)))
        assert str(request.url)=='https://openrouter.ai/api/v1/endpoints/zdr'
        assert request.headers['authorization']=='Bearer synthetic-test-key'
        return httpx.Response(200,json={'data':[
            {'model_id':'other/model','status':0,
             'supported_parameters':['structured_outputs','temperature','max_tokens']},
            {'model_id':'google/gemini-2.5-flash-lite','status':0,
             'supported_parameters':['response_format','temperature','max_tokens']},
        ]})
    actual=asyncio.run(verify_openrouter_zdr_model(
        'synthetic-test-key','google/gemini-2.5-flash-lite',
        transport=httpx.MockTransport(handle)))
    assert actual=={'verified':True,'model':'google/gemini-2.5-flash-lite','zdr_endpoint_count':1}
    assert len(calls)==1

    for payload in [
        {'data':[]},
        {'data':[{'model_id':'google/gemini-2.5-flash-lite','status':1,
                  'supported_parameters':['response_format','temperature','max_tokens']}]},
        {'data':[{'model_id':'google/gemini-2.5-flash-lite','status':0,
                  'supported_parameters':['temperature','max_tokens']}]},
        {'data':[{'model_id':'google/gemini-2.5-flash-lite','status':0,
                  'supported_parameters':['response_format','max_tokens']}]},
        {'data':{}},
    ]:
        with pytest.raises(ProviderFailure):
            asyncio.run(verify_openrouter_zdr_model(
                'synthetic-test-key','google/gemini-2.5-flash-lite',
                transport=httpx.MockTransport(lambda request,payload=payload:httpx.Response(200,json=payload))))
    for status in [401,500]:
        with pytest.raises(ProviderFailure):
            asyncio.run(verify_openrouter_zdr_model(
                'synthetic-test-key','google/gemini-2.5-flash-lite',
                transport=httpx.MockTransport(lambda request,status=status:httpx.Response(status,json={}))))
    with pytest.raises(ProviderFailure):
        asyncio.run(verify_openrouter_zdr_model('synthetic-test-key','openrouter/free'))
