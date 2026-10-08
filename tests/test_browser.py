"""UI integration in Chromium using explicit storage / network test adapters."""
import base64
import json
import os
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect
from browser.harness import mount, click,confirm,care_checks,practice_to_clean,ROOT
from conftest import ACCESS,make_image

@pytest.fixture(scope='module')
def browser():
    (ROOT/'evidence').mkdir(exist_ok=True)
    with sync_playwright() as p:
        executable=os.environ.get('GQ_CHROMIUM_EXECUTABLE','/usr/bin/chromium')
        args={'executable_path':executable} if Path(executable).exists() else {}
        b=p.chromium.launch(headless=True,args=['--no-sandbox'],**args)
        yield b;b.close()

@pytest.fixture
def page(browser):
    context=browser.new_context(viewport={'width':1440,'height':1050},reduced_motion='reduce')
    p=context.new_page();p.set_default_timeout(5000)
    yield p;context.close()

@pytest.mark.parametrize('width,height',[(1440,1050),(768,1024),(390,844),(320,740)])
def test_responsive_home_and_practice_clear(page,width,height):
    page.set_viewport_size({'width':width,'height':height});errors=mount(page)
    expect(page.locator('h1')).to_contain_text('A little mess.')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    if width in (1440,390):page.screenshot(path=str(ROOT/f'evidence/home-{ "desktop" if width==1440 else "mobile"}.png'),full_page=True)
    practice_to_clean(page)
    click(page,'practice-compare')
    expect(page.locator('main')).to_contain_text('300')
    expect(page.locator('.mode-banner')).to_contain_text('Practice mode')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    assert page.evaluate('GQ.stats(GQ.readStore(),"live").xp')==0
    assert page.evaluate('GQ.stats(GQ.readStore(),"practice").xp')==300
    if width in (1440,390):page.screenshot(path=str(ROOT/f'evidence/result-{ "desktop" if width==1440 else "mobile"}.png'),full_page=True)
    click(page,'finish');click(page,'journal')
    expect(page.locator('main')).to_contain_text('The grease gremlin')
    assert not errors,errors

def test_partial_retry_and_all_care_checks(page):
    mount(page);click(page,'practice-first');click(page,'confirm-target')
    expect(page.locator('#toast')).to_contain_text('Confirm the material')
    confirm(page);click(page,'choose-product','method-kitchen-clementine-uk-828');click(page,'prepare')
    click(page,'start-cleaning');expect(page.locator('#toast')).to_contain_text('all five')
    care_checks(page);click(page,'start-cleaning')
    page.locator('#practice-outcome').select_option('partial');click(page,'practice-compare')
    assert page.evaluate('GQ.stats(GQ.readStore(),"practice").xp')==0
    click(page,'retry');page.locator('#practice-outcome').select_option('clear');click(page,'practice-compare')
    assert page.evaluate('GQ.readStore().history.length')==1
    assert page.evaluate('GQ.stats(GQ.readStore(),"practice").xp')==300

@pytest.mark.parametrize('width',[390,320])
def test_expanded_catalog_loadout_has_no_mobile_overflow(page,width):
    page.set_viewport_size({'width':width,'height':844})
    mount(page);click(page,'practice-first');confirm(page)
    # Five reviewed products plus the deliberate unreviewed-product safety card.
    assert page.locator('[data-action="choose-product"]').count()==6
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
    expect(page.locator('main')).to_contain_text('Kiilto')

def test_mystery_surface_never_unlocks_product(page):
    mount(page);click(page,'scenario','mystery');confirm(page)
    # Cards remain explorable so the user can learn why they are unavailable.
    # No click may equip a product or reveal a prepare/start action.
    for card in page.locator('[data-action="choose-product"]').all():
        card.click()
        expect(page.locator('#toast')).to_contain_text('not supported')
        assert page.locator('[data-action="prepare"]').count()==0
    expect(page.locator('main')).to_contain_text('not supported')
    assert page.evaluate('GQ.stats(GQ.readStore(),"practice").xp')==0

def test_finland_catalog_brand_and_exact_variant_visible(page):
    mount(page);click(page,'inventory')
    expect(page.locator('main')).to_contain_text('Kiilto Ikkuna')
    expect(page.locator('main')).to_contain_text('600 ml · Finland')
    kiilto=page.locator('.catalog-item').filter(has_text='Kiilto Ikkuna').first
    expect(kiilto.locator('.bottle-body>span')).to_have_text('kiilto')

def test_arsenal_escaping_remove_and_private_export(page):
    errors=mount(page);click(page,'inventory')
    click(page,'add-catalog','method-kitchen-clementine-uk-828')
    click(page,'manual-product')
    dangerous='<img src=x onerror="window.PWNED=true">'
    page.locator('#product-name').fill(dangerous);page.locator('#product-note').fill('<script>window.PWNED=true</script>')
    click(page,'save-product')
    expect(page.locator('main')).to_contain_text(dangerous)
    assert page.evaluate('window.PWNED') is None
    assert page.evaluate('GQ.readStore().inventory.length')==2
    assert page.evaluate('GQ.readStore().inventory[1].catalogId') is None
    click(page,'remove-product',page.evaluate('GQ.readStore().inventory[1].id'))
    assert page.evaluate('GQ.readStore().inventory.length')==1
    assert 'data:image' not in page.evaluate('localStorage.getItem("grimequest.v1")')
    assert not errors

def test_corrupt_local_data_preserved_until_explicit_delete(page):
    mount(page,initial={'grimequest.v1':'corrupted-original'})
    expect(page.locator('body')).to_contain_text('original data is not overwritten')
    click(page,'settings');page.locator('summary').filter(has_text='Delete my local data').click()
    page.locator('[name="delete-confirm"]').check();click(page,'delete-data')
    assert page.evaluate('localStorage.getItem("grimequest.v1")') is None
    expect(page.locator('#toast')).to_contain_text('deleted')

def test_interrupted_live_task_blocks_new_quest(page):
    active={'version':1,'history':[],'inventory':[],'active':{'product':'Previously selected product','startedAt':'2026-10-06T00:00:00Z'}}
    mount(page,initial={'grimequest.v1':json.dumps(active)})
    click(page,'practice-first');expect(page.locator('#toast')).to_contain_text('interrupted live')
    click(page,'resolve-active');click(page,'clear-active');expect(page.locator('#toast')).to_contain_text('confirm')
    page.locator('[name="resolve-check"]').check();click(page,'clear-active')
    assert page.evaluate('GQ.readStore().active') is None

def setup_live(page,client):
    errors=mount(page,client);click(page,'settings')
    page.locator('#private-test-controls summary').click()
    page.locator('#access-code').fill(ACCESS);click(page,'save-code');click(page,'mode-live')
    click(page,'inventory');click(page,'add-catalog','method-kitchen-clementine-uk-828')
    click(page,'home');click(page,'find');return errors


def test_large_phone_camera_product_photo_is_downsampled_locally_without_upload(page,client):
    # Regresses the formerly rejected >12 MP camera import; no live AI call.
    mount(page,client)
    click(page,'inventory')
    click(page,'scan-product')
    data=make_image('white',size=(4032,3024))
    assert 4032*3024>12_000_000
    page.locator('#product-front').set_input_files({
        'name':'high-resolution-product.jpg','mimeType':'image/jpeg',
        'buffer':base64.b64decode(data.split(',')[1]),
    })
    thumb=page.locator('img[alt="Product Front label"]')
    expect(thumb).to_be_visible()
    assert thumb.evaluate('(img)=>img.naturalWidth===1600 && img.naturalHeight===1200')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')


def test_photo_pickers_offer_native_heic_and_heif(page,client):
    setup_live(page,client)
    accept=page.locator('#photo-file').get_attribute('accept')
    assert 'image/heic' in accept and 'image/heif' in accept
    assert 'image/jpeg' in accept and 'image/png' in accept
    click(page,'inventory');click(page,'scan-product')
    for item in ('product-front','product-back'):
        accepted=page.locator('#'+item).get_attribute('accept')
        assert 'image/heic' in accepted and 'image/heif' in accepted
        assert 'image/jpeg' in accepted


def upload(page,selector,data_url):
    page.locator(selector).set_input_files({'name':'synthetic-test.jpg','mimeType':'image/jpeg','buffer':base64.b64decode(data_url.split(',')[1])})
    page.wait_for_selector('img[alt="Selected image preview"]')

def test_public_demo_live_mode_needs_no_shared_code(page,settings,vision,before):
    from dataclasses import replace
    from fastapi.testclient import TestClient
    from server.app import create_app
    public=replace(settings,public_live=True,access_code='',max_calls_day=45)
    with TestClient(create_app(public,vision)) as c:
        errors=mount(page,c);click(page,'settings')
        expect(page.locator('main')).to_contain_text('Public demo access')
        assert page.locator('#access-code').count()==0
        click(page,'mode-live');click(page,'home');click(page,'find')
        upload(page,'#photo-file',before);page.locator('[name="photo-consent"]').check();click(page,'analyze-photo')
        page.wait_for_selector('#surface')
        assert vision.calls==['analyze']
        assert not errors,errors

def test_live_full_browser_api_flow_with_injected_vision(page,client,vision,before,after):
    errors=setup_live(page,client)
    upload(page,'#photo-file',before)
    click(page,'analyze-photo');expect(page.locator('#toast')).to_contain_text('approve')
    assert vision.calls==[]
    page.locator('[name="photo-consent"]').check();click(page,'analyze-photo')
    page.wait_for_selector('#surface');confirm(page)
    click(page,'choose-product','method-kitchen-clementine-uk-828');click(page,'prepare');care_checks(page);click(page,'start-cleaning')
    page.wait_for_selector('[data-action="capture-after"]')
    assert page.evaluate('GQ.readStore().active!==null')
    click(page,'capture-after');upload(page,'#photo-file',after)
    page.locator('[name="photo-consent"]').check();page.locator('[name="procedure-done"]').check();click(page,'analyze-photo')
    page.wait_for_selector('[data-action="finish"]')
    assert page.evaluate('GQ.stats(GQ.readStore(),"live").xp')==300
    assert page.evaluate('GQ.stats(GQ.readStore(),"practice").xp')==0
    assert page.evaluate('GQ.readStore().active') is None
    state=page.evaluate('localStorage.getItem("grimequest.v1")')
    assert 'data:image' not in state and ACCESS not in state
    assert vision.calls==['analyze','compare']
    assert not errors,errors

def test_live_removed_product_cannot_start(page,client,vision,before):
    setup_live(page,client)
    upload(page,'#photo-file',before);page.locator('[name="photo-consent"]').check();click(page,'analyze-photo')
    page.wait_for_selector('#surface');confirm(page)
    click(page,'choose-product','method-kitchen-clementine-uk-828')
    # Leave the quest, remove the exact reviewed product, then resume.
    click(page,'inventory')
    item_id=page.evaluate("GQ.readStore().inventory.find(i=>i.catalogId==='method-kitchen-clementine-uk-828').id")
    click(page,'remove-product',item_id)
    click(page,'home');click(page,'resume')
    assert page.locator('[data-action="prepare"]').count()==0
    expect(page.locator('main')).to_contain_text('No reviewed products in your arsenal yet')
    assert vision.calls==['analyze']

def test_bad_server_response_never_unlocks_or_awards(page,client,before):
    setup_live(page,client)
    page.evaluate('window.fetch=async()=>new Response(JSON.stringify({analysis:{surface:"magic"},target_ticket:"fake"}),{status:200,headers:{"content-type":"application/json"}})')
    upload(page,'#photo-file',before);page.locator('[name="photo-consent"]').check();click(page,'analyze-photo')
    expect(page.locator('#toast')).to_contain_text('Invalid target')
    assert page.evaluate('GQ.stats(GQ.readStore(),"live").xp')==0

def test_keyboard_focus_and_image_descriptions(page):
    mount(page)
    assert page.locator('img:not([alt])').count()==0
    assert page.locator('nav[aria-label="Main navigation"]').count()==1
    click(page,'practice-first')
    page.wait_for_timeout(100)
    assert page.evaluate('document.activeElement.tagName')=='H1'
    assert page.locator('select:not([id])').count()==0
    page.keyboard.press('Tab');assert page.evaluate('document.activeElement.tagName') in ['SELECT','BUTTON','A']

def test_export_payload_has_no_photos_or_access_code(page):
    mount(page);practice_to_clean(page);click(page,'practice-compare');click(page,'journal')
    page.evaluate('''() => {
      const original=URL.createObjectURL;
      URL.createObjectURL=function(blob){window.__exportBlob=blob;return original.call(URL,blob)};
      HTMLAnchorElement.prototype.click=function(){window.__exportName=this.download};
    }''')
    click(page,'export')
    text=page.evaluate('window.__exportBlob.text()');data=json.loads(text)
    assert data['format']=='grimequest-journal-v1' and len(data['history'])==1
    assert 'data:image' not in text and ACCESS not in text
    assert page.evaluate('window.__exportName')=='grimequest-journal.json'

def test_barcode_manual_product_never_needs_ocr_or_a_server(page):
    errors=mount(page)
    click(page,'inventory')
    click(page,'manual-product')
    expect(page.locator('h1')).to_contain_text('Find your bottle')
    expect(page.locator('main')).to_contain_text('NO LABEL OCR')
    assert page.locator('[data-action="read-label-ocr"]').count()==0
    assert page.locator('[name="product-consent"]').count()==0
    page.locator('#product-name').fill('Actual name from my bottle')
    page.locator('#product-note').fill('Read the manufacturer label first')
    click(page,'save-product')
    item=page.evaluate('GQ.readStore().inventory.at(-1)')
    assert item['name']=='Actual name from my bottle'
    assert item['catalogId'] is None
    assert 'barcode' not in item
    assert not errors


def test_ean_barcode_lookup_suggests_only_unreviewed_product(page):
    import importlib
    from fastapi.testclient import TestClient
    from server.barcodes import BarcodeSuggestion
    from server.config import Settings
    seen=[]
    class MockIndex:
        async def lookup(self,barcode):
            seen.append(barcode)
            return BarcodeSuggestion(barcode,True,'Kiilto Koti','Kiilto','600 ml')
    m=importlib.import_module('server.app')
    with TestClient(m.create_app(Settings(),barcode_lookup=MockIndex())) as client:
        errors=mount(page,client)
        click(page,'inventory');click(page,'scan-product')
        page.locator('#product-code').fill('4006381333931')
        click(page,'lookup-barcode')
        expect(page.locator('main')).to_contain_text('Community listing found')
        expect(page.locator('#product-name')).to_have_value('Kiilto Koti')
        expect(page.locator('main')).to_contain_text('600 ml')
        assert seen==['4006381333931']
        click(page,'save-product')
        expect(page.locator('#toast')).to_contain_text('Confirm the suggested name')
        page.locator('[name="barcode-review"]').check()
        click(page,'save-product')
        item=page.evaluate('GQ.readStore().inventory.at(-1)')
        assert item['barcode']=='4006381333931'
        assert item['catalogId'] is None
        assert 'data:image' not in page.evaluate("localStorage.getItem('grimequest.v1')")
        assert not errors


def test_missing_barcode_data_keeps_manual_gameplay(page):
    import importlib
    from fastapi.testclient import TestClient
    from server.barcodes import unknown
    from server.config import Settings
    class EmptyIndex:
        async def lookup(self,barcode):
            return unknown(barcode)
    m=importlib.import_module('server.app')
    with TestClient(m.create_app(Settings(),barcode_lookup=EmptyIndex())) as client:
        errors=mount(page,client)
        click(page,'inventory');click(page,'scan-product')
        page.locator('#product-code').fill('4006381333932')
        click(page,'lookup-barcode')
        expect(page.locator('#toast')).to_contain_text('check digit')
        page.locator('#product-code').fill('4006381333931')
        click(page,'lookup-barcode')
        expect(page.locator('main')).to_contain_text('No community record found')
        page.locator('#product-name').fill('Not indexed yet')
        click(page,'save-product')
        assert page.evaluate("GQ.readStore().inventory.at(-1).name")=='Not indexed yet'
        assert page.evaluate("GQ.readStore().inventory.at(-1).barcode")=='4006381333931'
        assert not errors


def test_zero_setup_guided_camera_full_game_without_ai_or_server_config(page,client,vision,before,after):
    errors=mount(page,client)
    assert page.locator('[data-action="guided-first"]').count() > 0
    click(page,'guided-first')
    upload(page,'#photo-file',before)
    page.locator('[name="guided-before-confirm"]').check()
    click(page,'guided-identify')
    page.locator('#surface').select_option('glazed_ceramic')
    page.locator('#soil').select_option('grease')
    page.locator('[name="surface-confirm"]').check()
    page.locator('[name="guided-safe-scene"]').check()
    click(page,'confirm-target')
    click(page,'choose-guided-method')
    expect(page.locator('main')).to_contain_text('Your own checked approach')
    click(page,'prepare')
    care_checks(page)
    click(page,'start-cleaning')
    page.wait_for_selector('[data-action="capture-after"]')
    click(page,'capture-after')
    upload(page,'#photo-file',after)
    page.locator('[name="guided-same-target"]').check()
    page.locator('[name="guided-dry"]').check()
    page.locator('#guided-outcome').select_option('clear')
    click(page,'guided-compare')
    expect(page.locator('main')).to_contain_text('SELF-REPORTED VISIBLE CHANGE')
    assert page.evaluate("GQ.readStore().history[0].mode")=='guided'
    assert page.evaluate("GQ.stats(GQ.readStore(),'guided').xp")==300
    assert page.evaluate("GQ.stats(GQ.readStore(),'live').xp")==0
    assert page.evaluate("GQ.stats(GQ.readStore(),'practice').xp")==0
    assert page.evaluate("GQ.readStore().active") is None
    assert 'data:image/' not in page.evaluate("localStorage.getItem('grimequest.v1')")
    assert vision.calls==[]
    assert not errors


def test_guided_quest_refuses_unsupported_material_and_duplicate_clear(page,client,vision,before,after):
    mount(page,client)
    click(page,'guided-first')
    upload(page,'#photo-file',before)
    page.locator('[name="guided-before-confirm"]').check()
    click(page,'guided-identify')
    page.locator('[name="surface-confirm"]').check()
    page.locator('[name="guided-safe-scene"]').check()
    click(page,'confirm-target')
    assert page.locator('[data-action="choose-guided-method"]').count()==0
    page.locator('[data-action="confirm-back"]').click()
    page.locator('#surface').select_option('uncoated_glass')
    page.locator('#soil').select_option('fingerprints')
    page.locator('[name="surface-confirm"]').check()
    page.locator('[name="guided-safe-scene"]').check()
    click(page,'confirm-target')
    click(page,'choose-guided-method');click(page,'prepare')
    care_checks(page);click(page,'start-cleaning');click(page,'capture-after')
    upload(page,'#photo-file',before)
    page.locator('[name="guided-same-target"]').check()
    page.locator('[name="guided-dry"]').check()
    page.locator('#guided-outcome').select_option('clear')
    click(page,'guided-compare')
    expect(page.locator('#toast')).to_contain_text('identical')
    assert page.evaluate("GQ.stats(GQ.readStore(),'guided').xp")==0
    assert vision.calls==[]

def test_ai_target_photo_can_be_reused_in_private_guided_quest(page,client,before):
    errors=setup_live(page,client)
    upload(page,'#photo-file',before)
    expect(page.locator('[data-action="guided-from-ai-photo"]')).to_be_visible()
    click(page,'guided-from-ai-photo')
    expect(page.locator('main')).to_contain_text('REAL CAMERA QUEST')
    expect(page.locator('img[alt="Selected image preview"]')).to_be_visible()
    assert page.evaluate('GQ.readStore().history.length')==0
    assert not errors

def _barcode_photo(code):
    """Generate an EAN-13 raster without invoking a third-party OCR engine."""
    from io import BytesIO
    from PIL import Image,ImageDraw
    left=["0001101","0011001","0010011","0111101","0100011",
          "0110001","0101111","0111011","0110111","0001011"]
    odd=["0100111","0110011","0011011","0100001","0011101",
         "0111001","0000101","0010001","0001001","0010111"]
    right=["1110010","1100110","1101100","1000010","1011100",
           "1001110","1010000","1000100","1001000","1110100"]
    patterns=["LLLLLL","LLGLGG","LLGGLG","LLGGGL","LGLLGG",
              "LGGLLG","LGGGLL","LGLGLG","LGLGGL","LGGLGL"]
    assert len(code)==13 and code.isdigit()
    bits="101"
    for d,p in zip(code[1:7],patterns[int(code[0])]):
        bits+=(left if p=="L" else odd)[int(d)]
    bits+="01010"
    for d in code[7:]:
        bits+=right[int(d)]
    bits+="101"
    unit=6;quiet=20
    width=(len(bits)+quiet*2)*unit
    image=Image.new('RGB',(width,280),'white')
    draw=ImageDraw.Draw(image)
    for i,value in enumerate(bits):
        if value=="1":
            x=(quiet+i)*unit
            draw.rectangle((x,12,x+unit-1,229),fill='black')
    output=BytesIO()
    image.save(output,'PNG')
    return output.getvalue()


def test_software_barcode_reader_auto_looks_up_photo_without_second_tap(page):
    """A locally decoded photo automatically performs a bounded GTIN lookup."""
    from fastapi.testclient import TestClient
    from server.app import create_app
    from server.config import Settings
    from server.barcodes import BarcodeSuggestion

    seen = []
    class Index:
        async def lookup(self,barcode):
            seen.append(barcode)
            return BarcodeSuggestion(barcode,True,'Example Cleaner 500 ml','Example','500 ml')

    with TestClient(create_app(Settings(),barcode_lookup=Index())) as client:
        errors=mount(page,client)
        page.add_script_tag(path=str(ROOT/'web/vendor/zxing-0.21.3.min.js'))
        click(page,'inventory');click(page,'scan-product')
        page.locator('#product-note').fill('My original note')
        page.locator('#barcode-photo').set_input_files({
            'name':'ean13.png','mimeType':'image/png',
            'buffer':_barcode_photo('4006381333931')
        })
        expect(page.locator('#product-code')).to_have_value('4006381333931')
        expect(page.locator('main')).to_contain_text('Possible product match')
        expect(page.locator('#product-name')).to_have_value('Example Cleaner 500 ml')
        expect(page.locator('#product-note')).to_have_value('My original note')
        assert seen==['4006381333931']
        assert not errors


def test_worldwide_name_search_selects_unreviewed_beauty_variant_without_ocr(page):
    """A global brand can be searched and selected without a readable barcode."""
    from fastapi.testclient import TestClient
    from server.app import create_app
    from server.config import Settings
    from server.barcodes import BarcodeSuggestion, unknown
    queries = []

    class GlobalIndex:
        async def search(self, term):
            queries.append(term)
            return [
                BarcodeSuggestion("036000291452", True, "Global Hand Soap", "Worldwide", "500 ml",
                                  "Open Beauty Facts", "beauty"),
                BarcodeSuggestion("4006381333931", True, "Global Cleaner", "Worldwide", "750 ml"),
            ]
        async def lookup(self, barcode):
            return unknown(barcode)

    with TestClient(create_app(Settings(), barcode_lookup=GlobalIndex())) as client:
        errors=mount(page,client)
        click(page,"inventory")
        click(page,"scan-product")
        assert page.locator('[data-action="read-label-ocr"]').count()==0
        assert page.locator('[name="product-consent"]').count()==0
        page.locator('#product-note').fill('Keep my personal manual notes')
        page.locator('#product-search').fill('Global')
        click(page,'search-product-name')
        expect(page.locator('main')).to_contain_text('Found 2 possible products')
        expect(page.locator('main')).to_contain_text('Open Beauty Facts')
        assert queries==['Global']
        assert page.locator('#product-note').input_value()=='Keep my personal manual notes'
        click(page,'select-search-result','0')
        expect(page.locator('#product-name')).to_have_value('Global Hand Soap')
        expect(page.locator('#product-code')).to_have_value('036000291452')
        expect(page.locator('main')).to_contain_text('Open Beauty Facts source')
        click(page,'save-product')
        expect(page.locator('#toast')).to_contain_text('Confirm the suggested name')
        page.locator('[name="barcode-review"]').check()
        click(page,'save-product')
        item=page.evaluate("GQ.readStore().inventory.at(-1)")
        assert item['name']=='Global Hand Soap'
        assert item['barcode']=='036000291452'
        assert item['note']=='Keep my personal manual notes'
        assert item['catalogId'] is None
        assert 'data:image' not in page.evaluate("localStorage.getItem('grimequest.v1')")
        assert not errors


def test_global_name_search_in_unicode_with_no_record_has_manual_path(page):
    """International scripts work and missing data must not block the game."""
    from fastapi.testclient import TestClient
    from server.app import create_app
    from server.config import Settings
    from server.barcodes import unknown
    queries=[]

    class SparseIndex:
        async def search(self,term):
            queries.append(term)
            return []
        async def lookup(self,barcode):
            return unknown(barcode)

    with TestClient(create_app(Settings(), barcode_lookup=SparseIndex())) as client:
        errors=mount(page,client)
        click(page,'inventory');click(page,'scan-product')
        page.locator('#product-search').fill('洗衣粉')
        click(page,'search-product-name')
        expect(page.locator('main')).to_contain_text('No matching entries')
        assert queries==['洗衣粉']
        page.locator('#product-name').fill('洗衣粉 Brand')
        click(page,'save-product')
        item=page.evaluate('GQ.readStore().inventory.at(-1)')
        assert item['name']=='洗衣粉 Brand'
        assert 'barcode' not in item
        assert item['catalogId'] is None
        assert not errors

