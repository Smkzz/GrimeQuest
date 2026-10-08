"""Public monster-game regressions, with synthetic image fixtures, no paid/network providers."""
import base64
import json
from pathlib import Path
import pytest
from playwright.sync_api import expect
from test_browser import browser, page  # existing real Chromium fixtures
from browser.harness import mount, ROOT


def tap(page, action):
    page.locator(f'[data-quick="{action}"]').first.click()


def photo(page, value, after=False):
    page.locator('#quick-file').set_input_files({
        'name':'synthetic-after.jpg' if after else 'synthetic-before.jpg',
        'mimeType':'image/jpeg', 'buffer':base64.b64decode(value.split(',')[1])
    })
    label='After photo preview' if after else 'Before photo preview'
    expect(page.locator(f'img[alt="{label}"]')).to_be_visible()


def complete(page, before, after):
    tap(page,'start'); photo(page,before); tap(page,'before-ready')
    tap(page,'after'); photo(page,after,True); tap(page,'claim')
    expect(page.locator('h1')).to_contain_text('Grime defeated')


@pytest.mark.parametrize('width,height',[(320,740),(390,844),(1440,1000)])
def test_monster_demo_entire_loop_has_no_points_no_camera_no_api(page,width,height):
    page.set_viewport_size({'width':width,'height':height})
    errors=mount(page,casual=True)
    page.evaluate('''() => {window.__network=0;window.fetch=()=>{window.__network++;throw Error('Demo must be offline');};}''')
    saved=page.evaluate("localStorage.getItem('grimequest.v1')")
    for _ in range(2):
        tap(page,'demo')
        expect(page.locator('.gq-demo-banner')).to_contain_text('NO XP')
        assert page.locator('#quick-file').count()==0
        assert page.locator('#surface').count()==0
        assert page.locator('#product-code').count()==0
        tap(page,'after');tap(page,'claim')
        expect(page.locator('.gq-demo-proof')).to_contain_text('No points, wins or creatures')
        assert page.evaluate('GQ.monsterProgress(GQ.readStore()).xp')==0
        assert page.evaluate('GQ.monsterProgress(GQ.readStore()).collected.length')==0
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth')
        tap(page,'demo-exit')
    assert page.evaluate('window.__network')==0
    assert page.evaluate("localStorage.getItem('grimequest.v1')")==saved
    assert errors==[]


def test_real_photo_quest_unlocks_creature_and_next_is_different(page,before,after):
    errors=mount(page,casual=True)
    complete(page,before,after)
    expect(page.locator('.gq-unlock')).to_contain_text('Smudgie')
    expect(page.locator('.gq-unlock')).to_contain_text('NEW CREATURE COLLECTED')
    assert page.evaluate('GQ.monsterProgress(GQ.readStore()).collected')==['smudgie']
    assert page.evaluate("GQ.stats(GQ.readStore(),'guided').xp")==300
    assert page.evaluate("GQ.stats(GQ.readStore(),'live').xp")==0
    assert 'data:image' not in page.evaluate("localStorage.getItem('grimequest.v1')")
    tap(page,'home')
    expect(page.locator('.gq-opponent')).to_contain_text('Dusty')
    tap(page,'wins')
    assert page.locator('.gq-collection-card.collected').count()==1
    assert page.locator('.gq-collection-card.locked').count()==5
    assert errors==[]


def test_collect_all_six_and_level_up_without_bonus_or_duplicate_xp(page,before,after):
    mount(page,casual=True)
    names=['Smudgie','Dusty','Crumb Goblin','Splodge','Grubble','Lord Grime']
    for i,name in enumerate(names):
        complete(page,before,after)
        expect(page.locator('.gq-unlock')).to_contain_text(name)
        assert page.evaluate('GQ.readStore().history.length')==i+1
        assert page.evaluate("GQ.stats(GQ.readStore(),'guided').xp")==(i+1)*300
        if i==2: expect(page.locator('.gq-result-level')).to_contain_text('Level up! Level 2')
        # A duplicate action cannot issue another reward after the result phase.
        page.evaluate("() => {const b=document.createElement('button');b.dataset.quick='claim';document.querySelector('#app').append(b);b.click();b.remove();}")
        assert page.evaluate('GQ.readStore().history.length')==i+1
    tap(page,'wins')
    assert page.locator('.gq-collection-card.collected').count()==6
    assert page.locator('.gq-collection-card.locked').count()==0
    assert page.evaluate('GQ.monsterProgress(GQ.readStore()).level')==3


def test_reveal_is_keyboard_operable_and_does_not_mutate_photos(page,before,after):
    mount(page,casual=True);complete(page,before,after)
    images=page.locator('.gq-reveal img').evaluate_all('(els)=>els.map(e=>e.src)')
    control=page.get_by_role('slider',name='Slide to compare before and after photos')
    control.focus();control.press('ArrowRight')
    expect(control).to_have_value('51')
    expect(control).to_have_attribute('aria-valuetext','51 percent of before photo visible')
    assert page.locator('.gq-reveal').evaluate("e=>e.style.getPropertyValue('--reveal')")=='51%'
    assert images==page.locator('.gq-reveal img').evaluate_all('(els)=>els.map(e=>e.src)')
    assert page.evaluate('GQ.readStore().history.length')==1


def test_alignment_guide_is_optional_and_never_changes_recorded_image(page,before,after):
    mount(page,casual=True);tap(page,'start');photo(page,before);tap(page,'before-ready');tap(page,'after')
    tap(page,'align');assert page.locator('.gq-alignment').count()==1
    tap(page,'align');assert page.locator('.gq-alignment').count()==0
    photo(page,after,True)
    preview=page.locator('img[alt="After photo preview"]').get_attribute('src')
    tap(page,'align');tap(page,'claim')
    assert page.locator('.gq-reveal-after img').get_attribute('src')==preview
    assert page.evaluate('GQ.readStore().history.length')==1


def test_discard_requires_confirmation_and_keyboard_escape_preserves_quest(page,before):
    mount(page,casual=True);tap(page,'start');photo(page,before);tap(page,'before-ready')
    tap(page,'discard')
    expect(page.get_by_role('dialog',name='Discard unfinished quest')).to_be_visible()
    expect(page.locator('[data-quick="discard-cancel"]')).to_be_focused()
    page.keyboard.press('Escape')
    assert page.get_by_role('dialog').count()==0
    expect(page.locator('h1')).to_contain_text('Time to clean')
    tap(page,'discard');tap(page,'discard-confirm')
    expect(page.locator('h1')).to_contain_text('A little mess')
    assert page.locator('[data-quick="resume"]').count()==0
    assert page.evaluate('GQ.readStore().history.length')==0


def test_win_share_is_user_initiated_text_only_with_explicit_provenance(page,before,after):
    mount(page,casual=True)
    page.evaluate("() => {window.__shares=[];Object.defineProperty(navigator,'share',{value:async x=>{window.__shares.push(x)},configurable:true});}")
    complete(page,before,after)
    assert page.evaluate('window.__shares.length')==0
    tap(page,'share')
    payload=page.evaluate('window.__shares[0]')
    assert set(payload)=={'title','text','url'}
    assert 'self-reported' in payload['text']
    assert payload['url']=='https://grimequest-web-production.up.railway.app/'
    assert 'data:image' not in json.dumps(payload)
    assert 'files' not in payload
    assert page.evaluate('GQ.readStore().history.length')==1


def test_reduced_motion_disables_character_and_confetti_animations(page):
    mount(page,casual=True)
    assert page.locator('.gq-hero-monster').evaluate('e=>getComputedStyle(e).animationName')=='none'
    tap(page,'demo');tap(page,'after');tap(page,'claim')
    assert page.locator('.gq-confetti').evaluate('e=>getComputedStyle(e).display')=='none'


def test_historical_guided_points_do_not_invent_monster_encounters(page):
    initial={'grimequest.v1':json.dumps({'version':1,'history':[{'id':'previous','name':'Grime defeated','room':'Home','mode':'guided','status':'clear','xp':300,'date':'2026-10-08T12:00:00Z'}],'inventory':[],'active':None})}
    mount(page,initial=initial,casual=True)
    state=page.evaluate('GQ.monsterProgress(GQ.readStore())')
    assert state['xp']==300 and state['collected']==[] and state['next']['id']=='smudgie'
    tap(page,'wins');expect(page.locator('.gq-journal')).to_contain_text('Grime defeated')


def test_progress_never_counts_ai_practice_or_partial_as_collection(page):
    mount(page,casual=True)
    results=page.evaluate('''() => {
      const s=GQ.emptyStore();
      for(const mode of ['practice','live','guided'])s.history.push({id:mode,name:'Grime defeated · Smudgie',room:'x',mode,status:mode==='guided'?'partial':'clear',xp:mode==='guided'?0:300,date:new Date().toISOString()});
      const r=GQ.monsterProgress(s);return {xp:r.xp,collected:r.collected,next:r.next.id};
    }''')
    assert results=={'xp':0,'collected':[],'next':'smudgie'}


def test_public_game_stylesheet_is_built_precached_and_standalone_inlined():
    sw=(ROOT/'web/sw.js').read_text()
    assert '"/game.css"' in sw
    preview=(ROOT/'preview.html').read_text()
    assert 'class="monster-game"' in preview
    assert '.gq-reveal' in preview
    assert '<link rel="stylesheet" href="game.css">' not in preview


def test_monster_does_not_change_after_visiting_menu_mid_quest(page,before,after):
    mount(page,casual=True);tap(page,'start');photo(page,before);tap(page,'before-ready')
    expect(page.locator('.gq-battle-quote')).to_contain_text('comfortable')
    tap(page,'wins');tap(page,'resume')
    expect(page.locator('.gq-battle-quote')).to_contain_text('comfortable')
    tap(page,'after');photo(page,after,True);tap(page,'settings');tap(page,'resume');tap(page,'claim')
    expect(page.locator('.gq-unlock')).to_contain_text('Smudgie')
    assert page.evaluate('GQ.monsterProgress(GQ.readStore()).collected')==['smudgie']
