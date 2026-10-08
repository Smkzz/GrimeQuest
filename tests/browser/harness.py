"""Browser harness for an environment that blocks URL navigation by policy.

Generated standalone HTML is injected with set_content; memory-backed Storage
and a Python TestClient fetch bridge isolate the application from browser network
and persistence. This does NOT test real installation, TLS, hardware or browser
origin enforcement; those remain explicit physical-device release checks.
"""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SHIM='''
const NativeDate=Date;window.Date=class extends NativeDate{constructor(...a){super(...(a.length?a:['2026-10-06T12:00:00Z']));}static now(){return new NativeDate('2026-10-06T12:00:00Z').getTime();}};
window.__testStorage={local:{},session:{}};
function testStorage(kind){const d=window.__testStorage[kind];return {getItem:k=>d[k]??null,setItem:(k,v)=>{d[k]=String(v)},removeItem:k=>{delete d[k]},clear:()=>{Object.keys(d).forEach(k=>delete d[k])},key:i=>Object.keys(d)[i]??null,get length(){return Object.keys(d).length}}}
Object.defineProperty(window,'localStorage',{value:testStorage('local'),configurable:true});
Object.defineProperty(window,'sessionStorage',{value:testStorage('session'),configurable:true});
if(!crypto.randomUUID)crypto.randomUUID=()=>[...crypto.getRandomValues(new Uint8Array(16))].map(x=>x.toString(16).padStart(2,'0')).join('');
window.fetch=async(path,options={})=>{if(typeof path!=='string'||!path.startsWith('/api/'))throw Error('Test bridge only accepts relative API paths');const r=await window.__testFetch(path,options);return new Response(r.body,{status:r.status,headers:r.headers})};
'''

def mount(page,client=None,initial=None,casual=False):
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)))
    def fetch_bridge(path,options):
        if client is None:
            return {'status':200,'headers':{'content-type':'application/json'},'body':json.dumps({'live_ready':False,'version':'0.1.0','provider_host':None,'provider_model':None,'max_calls_hour':40,'max_calls_day':200,'access_mode':'private_code'})}
        headers={**options.get('headers',{}),'origin':'http://testserver'}
        response=client.request(options.get('method','GET'),path,headers=headers,content=options.get('body'))
        return {'status':response.status_code,'headers':dict(response.headers),'body':response.text}
    page.expose_function('__testFetch',fetch_bridge)
    state=('window.__GQ_ARCHIVE_TEST__='+('false' if casual else 'true')+';') + ('' if initial is None else 'Object.assign(window.__testStorage.local,'+json.dumps(initial)+');')
    html=(ROOT/'preview.html').read_text().replace('<head>','<head><script>'+SHIM+state+'</script>',1)
    page.set_content(html,wait_until='domcontentloaded')
    page.wait_for_selector('[data-quick="start"]' if casual else '[data-action="practice-first"]')
    page.wait_for_timeout(100)
    return errors

def click(page,action,ident=None):
    selector=f'[data-action="{action}"]'+(f'[data-id="{ident}"]' if ident else '')
    page.locator(selector).first.click()

def confirm(page):
    page.locator('[name="surface-confirm"]').check();click(page,'confirm-target')

def care_checks(page):
    for name in ['exact_product','label_allows_target','surface_care_allows','no_other_product','cool_and_safe']:
        page.locator(f'[name="{name}"]').check()

def practice_to_clean(page,scenario='kitchen'):
    click(page,'scenario',scenario);confirm(page)
    click(page,'choose-product','method-kitchen-clementine-uk-828' if scenario=='kitchen' else 'method-glass-mint-uk-828')
    click(page,'prepare');care_checks(page);click(page,'start-cleaning')
