"""Synthetic fixtures: these are deliberately NOT real-world cleaning evidence."""
import base64
import io
import pytest
from datetime import date
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from server.app import create_app
from server.config import Settings
from server.models import TargetAnalysis, ProductObservation, Comparison, Attestations

ACCESS = 'test-only-access-code-with-32-characters'
HEADERS = {'origin':'http://testserver','x-gq-access':ACCESS}
PRODUCT = 'method-kitchen-clementine-uk-828'

def make_image(color='white', fmt='JPEG', size=(160,120), mark=False, exif=None):
    im=Image.new('RGB',size,color)
    if mark: ImageDraw.Draw(im).ellipse((20,20,80,70),fill='brown')
    out=io.BytesIO();kwargs={'exif':exif} if exif else {}
    im.save(out,fmt,**kwargs)
    return f'data:image/{"jpeg" if fmt=="JPEG" else fmt.lower()};base64,'+base64.b64encode(out.getvalue()).decode()

@pytest.fixture
def before(): return make_image('white',mark=True)
@pytest.fixture
def after(): return make_image('white')
@pytest.fixture
def attestations(): return Attestations(**{k:True for k in Attestations.model_fields})
@pytest.fixture
def analysis():
    return TargetAnalysis(object_name='Tiled splashback',surface='glazed_ceramic',soil='grease',visible_soil=True,image_quality='usable',material_certainty='tentative',hazards=['none'],target_box={'x':0.1,'y':0.1,'width':0.8,'height':0.8})
@pytest.fixture
def clear():
    return Comparison(same_target=True,comparable=True,visible_soil_before=True,residue_after='not_visible',improvement='substantial',wet_or_glare=False,obstructed=False)

class FakeVision:
    """Injectable observation component. No network or safety expertise."""
    def __init__(self,analysis,comparison):
        self.analysis,self.comparison=analysis,comparison
        self.calls=[];self.failure=None
    def check(self,kind):
        self.calls.append(kind)
        if self.failure: raise self.failure
    async def analyze(self,image):
        self.check('analyze');return self.analysis
    async def product(self,front,back):
        self.check('product')
        return ProductObservation(name='Unreviewed bottle',label_readable=True,label_text='Use on specified surfaces only',warnings_observed=['Read the current label'])
    async def compare(self,before,after):
        self.check('compare');return self.comparison

@pytest.fixture
def vision(analysis,clear): return FakeVision(analysis,clear)
@pytest.fixture
def settings(): return Settings(provider_base='https://vision.example/v1',provider_model='test-model',provider_key='fake-secret-not-a-credential',access_code=ACCESS,ticket_secret='t'*48,max_calls_hour=100)
@pytest.fixture
def client(settings,vision):
    with TestClient(create_app(settings,provider=vision)) as c: yield c

def start_encounter(client,before,attestations):
    result=client.post('/api/analyze-target',headers=HEADERS,json={'image':before,'consent':True})
    assert result.status_code==200,result.text
    response=client.post('/api/start',headers=HEADERS,json={'target_ticket':result.json()['target_ticket'],'surface':'glazed_ceramic','soil':'grease','product_id':PRODUCT,'attestations':attestations.model_dump()})
    assert response.status_code==200,response.text
    return response.json()

def verify(client,encounter,before,after,**overrides):
    body={'encounter_ticket':encounter['encounter_ticket'],'before_image':before,'after_image':after,'consent':True,'procedure_completed':True,'surface_dry':True,**overrides}
    return client.post('/api/verify',headers=HEADERS,json=body)

@pytest.fixture(autouse=True)
def catalog_fixture_clock(monkeypatch):
    class FixtureDate(date):
        @classmethod
        def today(cls): return cls(2026,10,6)
    monkeypatch.setattr('server.policy.date',FixtureDate)
