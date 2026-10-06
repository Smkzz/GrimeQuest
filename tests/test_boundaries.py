import asyncio
import base64
import io
import json
from dataclasses import replace
import pytest
from PIL import Image
from fastapi import HTTPException
from server.app import Budget,create_app
from server.config import Settings
from server.images import normalize_image, InvalidImage
from server.tickets import Tickets,InvalidTicket
from fastapi.testclient import TestClient
from conftest import make_image,HEADERS,ACCESS

@pytest.mark.parametrize('fmt',['JPEG','PNG','WEBP'])
def test_image_canonicalization(fmt):
    raw=make_image('gray',fmt=fmt,size=(1800,1200))
    clean=normalize_image(raw)
    assert clean.data_url.startswith('data:image/jpeg;base64,')
    assert clean.width==1600 and clean.height<=1600 and len(clean.digest)==64
    assert clean==normalize_image(raw)

@pytest.mark.parametrize('value',['data:image/svg+xml;base64,'+'x'*100,'data:image/jpeg;base64,'+'!'*80,'http://example.com/image.jpg','x'*2_800_001,make_image(size=(63,100)),make_image('white','PNG').replace('image/png','image/jpeg'),'data:image/jpeg;base64,'+base64.b64encode(b'not an image'*10).decode()])
def test_reject_bad_images(value):
    with pytest.raises(InvalidImage):normalize_image(value)

def test_metadata_is_stripped():
    exif=Image.Exif();exif[0x010e]='PRIVATE description';exif[0x0112]=6
    clean=normalize_image(make_image(size=(160,120),exif=exif))
    with Image.open(io.BytesIO(base64.b64decode(clean.data_url.split(',')[1]))) as im:
        assert not im.getexif() and im.size==(120,160)
    assert b'PRIVATE' not in base64.b64decode(clean.data_url.split(',')[1])

def test_pixel_limit_and_animated():
    with pytest.raises(InvalidImage):normalize_image(make_image(size=(4000,3100)))
    out=io.BytesIO();im=Image.new('RGB',(80,80),'white');im.save(out,'WEBP',save_all=True,append_images=[Image.new('RGB',(80,80),'black')],duration=100)
    with pytest.raises(InvalidImage):normalize_image('data:image/webp;base64,'+base64.b64encode(out.getvalue()).decode())

def test_alpha_is_flattened():
    im=Image.new('RGBA',(100,100),(0,0,0,0));out=io.BytesIO();im.save(out,'PNG')
    result=normalize_image('data:image/png;base64,'+base64.b64encode(out.getvalue()).decode())
    with Image.open(io.BytesIO(base64.b64decode(result.data_url.split(',')[1]))) as clean:assert clean.getpixel((5,5))==(255,255,255)

def test_tickets_expiry_binding_and_restart():
    now=[1000.0];t=Tickets(b'a'*32,clock=lambda:now[0]);token=t.sign('target',{'id':'42'},ttl=5)
    assert t.read(token,'target')=={'id':'42'}
    for bad,purpose in [(token,'completion'),(token+'x','target'),('x'*14001,'target'),('bad','target')]:
        with pytest.raises(InvalidTicket):t.read(bad,purpose)
    with pytest.raises(InvalidTicket):Tickets(b'b'*32).read(token,'target')
    now[0]=1005
    with pytest.raises(InvalidTicket):t.read(token,'target')

@pytest.mark.parametrize('url',['http://remote.example/v1','https://user:password@example.com/v1','https://example.com/v1?api_key=secret','file:///etc/passwd','https://example.com/#fragment','ftp://example.com'])
def test_config_rejects_unsafe_bases(url):
    with pytest.raises(ValueError):Settings(provider_base=url).validate()

def test_config_loopback_explicit_only():
    with pytest.raises(ValueError):Settings(provider_base='http://127.0.0.1:1234/v1').validate()
    assert Settings(provider_base='http://127.0.0.1:1234/v1',allow_local_provider=True).validate()
    assert not Settings(provider_base='https://example.com',provider_model='a',access_code='short').ready

@pytest.mark.parametrize('origin',['http://example.com','https://example.com/path','https://user@example.com','https://example.com?x=1'])
def test_origin_configuration(origin):
    with pytest.raises(ValueError):Settings(app_origin=origin).validate()

@pytest.mark.parametrize('limit',[0,-1,1001])
def test_bad_call_limit(limit):
    with pytest.raises(ValueError):Settings(max_calls_hour=limit).validate()

def test_default_is_off_and_private_headers():
    with TestClient(create_app(Settings())) as c:
        health=c.get('/api/health');assert not health.json()['live_ready']
        assert health.headers['cache-control']=='no-store'
        assert 'frame-ancestors' in health.headers['content-security-policy']
        assert c.get('/').status_code==200
        assert c.get('/sw.js').headers['cache-control']=='no-cache'
        assert c.post('/api/analyze-target',headers=HEADERS,json={}).status_code==503
        assert c.get('/api/catalog').json()['products']
        assert c.get('/api/health',headers={'host':'attacker.example'}).status_code==400
        assert c.get('/.env').status_code==404
        assert c.get('/server/catalog.json').status_code==404

@pytest.mark.parametrize('headers,status',[({},403),({'origin':'https://evil.example','x-gq-access':ACCESS},403),({'origin':'http://testserver','x-gq-access':'wrong'},401),({**HEADERS,'sec-fetch-site':'cross-site'},403),({**HEADERS,'content-type':'text/plain'},415),({**HEADERS,'content-length':'6000000'},413),({**HEADERS,'content-length':'-1'},413),({**HEADERS,'content-length':'invalid'},400)])
def test_api_boundary_rejects_before_model(client,vision,headers,status):
    r=client.post('/api/analyze-target',headers=headers,json={})
    assert r.status_code==status,r.text
    assert vision.calls==[]

def test_validation_does_not_reflect_input(client):
    r=client.post('/api/analyze-target',headers=HEADERS,json={'image':'PRIVATE_SECRET','consent':True})
    assert r.status_code==422 and 'PRIVATE_SECRET' not in r.text

def test_global_per_client_and_concurrent_budget():
    async def run():
        b=Budget(3)
        async with b.slot('a'):
            async with b.slot('b'):
                with pytest.raises(HTTPException):
                    async with b.slot('c'):pass
        assert b.active==0
        async with b.slot('a'):pass
        with pytest.raises(HTTPException):
            async with b.slot('d'):pass
        assert len(b.events)==3
        b=Budget(100)
        for _ in range(20):
            async with b.slot('same'):pass
        with pytest.raises(HTTPException):
            async with b.slot('same'):pass
        async with b.slot('different'):pass
        assert b.active==0
    asyncio.run(run())

def test_budget_releases_on_failure_and_expiry(monkeypatch):
    async def run():
        b=Budget(1)
        with pytest.raises(ValueError):
            async with b.slot('a'):raise ValueError('failure')
        assert b.active==0
        b.events[0]=(0,'a')
        monkeypatch.setattr('server.app.time.monotonic',lambda:4000)
        async with b.slot('a'):pass
        assert len(b.events)==1
    asyncio.run(run())

@pytest.mark.parametrize('variant,expected',[('large',413),('replay',200),('disconnect',None),('bad-token',401)])
def test_raw_asgi_chunked_boundaries(settings,variant,expected):
    from server.app import Boundary
    async def run():
        sent=[];calls=[]
        chunks=([{'type':'http.request','body':b'x'*3_000_000,'more_body':True},{'type':'http.request','body':b'x'*3_000_000,'more_body':False}]
                if variant=='large' else [{'type':'http.request','body':b'{','more_body':True},{'type':'http.request','body':b'}','more_body':False}])
        if variant=='disconnect':chunks=[{'type':'http.disconnect'}]
        async def receive():return chunks.pop(0) if chunks else {'type':'http.disconnect'}
        async def send(message):sent.append(message)
        async def app(scope,receive,send):
            calls.append(await receive());assert (await receive())['type']=='http.disconnect'
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'{}'})
        scope={'type':'http','method':'POST','path':'/api/test','headers':[(b'host',b'testserver'),(b'origin',b'http://testserver'),(b'content-type',b'application/json'),(b'x-gq-access',b'\xff' if variant=='bad-token' else ACCESS.encode())]}
        await Boundary(app,settings)(scope,receive,send)
        statuses=[m['status'] for m in sent if m['type']=='http.response.start']
        assert statuses==([] if expected is None else [expected])
        assert bool(calls)==(variant=='replay')
        if calls:assert calls[0]['body']==b'{}'
    asyncio.run(run())

def test_configured_external_origin_https_headers(settings,vision):
    configured=replace(settings,app_origin='https://grime.example/')
    with TestClient(create_app(configured,vision),base_url='https://grime.example') as c:
        h=c.get('/api/health');assert h.status_code==200
        assert 'max-age' in h.headers['strict-transport-security']
        r=c.post('/api/match',headers={'origin':'https://grime.example','x-gq-access':ACCESS},json={})
        assert r.status_code==422 # Passed origin check; empty payload is invalid.
