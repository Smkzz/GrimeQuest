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

def test_label_scan_is_wired_and_never_auto_authorized(page,client,vision,before,after):
    setup_live(page,client);click(page,'inventory');click(page,'scan-product')
    for field,data in [('product-front',before),('product-back',after)]:
        page.locator('#'+field).set_input_files({'name':'label.jpg','mimeType':'image/jpeg','buffer':base64.b64decode(data.split(',')[1])})
        page.wait_for_timeout(150)
    page.locator('[name="product-consent"]').check();click(page,'analyze-product')
    expect(page.locator('#product-name')).to_have_value('Unreviewed bottle')
    click(page,'save-product')
    assert page.evaluate('GQ.readStore().inventory.at(-1).catalogId') is None
    assert vision.calls==['product']

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
