"""Reproducible static build: compile TS, make offline assets and a standalone preview."""
from pathlib import Path
import base64
import hashlib
import json
import shutil
import subprocess
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
ASSETS = WEB / "assets"


def create_art():
    ASSETS.mkdir(exist_ok=True)
    # Original UI fixture illustrations; never presented as photographs.
    def scene(kind, condition):
        header='<svg xmlns="http://www.w3.org/2000/svg" width="640" height="440" viewBox="0 0 640 440"><title>GrimeQuest illustrated practice scene</title>'
        if kind=='kitchen':
            base='<rect width="640" height="440" fill="#eee8db"/><rect x="54" y="35" width="532" height="313" rx="8" fill="#f7f4e9" stroke="#dddccb" stroke-width="7"/>'
            for x in [185,318,451]: base+=f'<path d="M{x} 38v307" stroke="#dddccb" stroke-width="5"/>'
            for y in [139,243]: base+=f'<path d="M56 {y}h529" stroke="#dddccb" stroke-width="5"/>'
            base+='<path d="M0 362h640v78H0" fill="#d4c6b0"/><path d="M0 362h640" stroke="#c7b89f" stroke-width="9"/><ellipse cx="501" cy="359" rx="51" ry="11" fill="#b9bba5"/><rect x="473" y="297" width="57" height="61" rx="7" fill="#74976b"/><path d="M503 300c-55-15-61-52-27-48 18 1 23 24 27 48M502 293c49-17 44-49 19-41-18 6-19 41-19 41" fill="#91ad7c"/>'
            spots=[(135,103,30,19),(319,187,37,27),(238,291,29,17),(418,112,24,13),(144,204,12,8),(377,281,14,9)]
            if condition=='partial': spots=spots[:2]
            if condition=='after': spots=[]
            for x,y,rx,ry in spots:
                base+=f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="#ba966d" opacity=".62" transform="rotate(-15 {x} {y})"/><circle cx="{x+rx+8}" cy="{y+ry}" r="4" fill="#ba966d" opacity=".65"/>'
        elif kind=='glass':
            base='<rect width="640" height="440" fill="#e0ebe1"/><rect x="99" y="30" width="441" height="337" rx="12" fill="#c4dedb" stroke="#f8faf0" stroke-width="15"/><path d="M110 285q89-111 175-22t134-43q51-30 110 9v127H110Z" fill="#a4c0a0"/><path d="M110 320q73-31 140 0t131-21 148 22v34H110Z" fill="#8cad8f"/><circle cx="447" cy="99" r="37" fill="#f7e9bb"/><path d="M320 38v322M107 195h425" stroke="#f8faf0" stroke-width="13"/><path d="m140 73 102 0-102 113Z" fill="#ffffff26"/><rect x="78" y="367" width="484" height="21" rx="6" fill="#bcc9b4"/><path d="M0 423h640v17H0" fill="#cad7c4"/>'
            spots=[(217,125),(404,282),(241,299)]
            if condition=='partial':spots=spots[:1]
            if condition=='after':spots=[]
            for x,y in spots:
                base+=f'<g transform="translate({x} {y}) rotate(-17)" fill="#95a99a" opacity=".64"><ellipse rx="22" ry="26"/><rect x="-23" y="-48" width="9" height="39" rx="5"/><rect x="-10" y="-58" width="9" height="45" rx="5"/><rect x="3" y="-55" width="9" height="44" rx="5"/><rect x="16" y="-43" width="8" height="38" rx="4"/><ellipse cx="-27" cy="-6" rx="9" ry="18" transform="rotate(-30 -27 -6)"/></g>'
        else:
            base='<rect width="640" height="440" fill="#e9e4ee"/><rect x="74" y="94" width="494" height="260" rx="19" fill="#d7d2de" stroke="#c6c0d1" stroke-width="3"/><path d="M80 170q140-90 203 23t278-35M76 280q142-84 256-1t232 13M203 99q-17 63 57 136t35 116" fill="none" stroke="#bdb5c7" stroke-width="5"/><ellipse cx="326" cy="236" rx="44" ry="30" fill="#aca3b7" opacity=".6"/><circle cx="322" cy="199" r="57" fill="#f8f5fb" stroke="#d2c9df" stroke-width="3"/><text x="322" y="223" font-family="sans-serif" font-size="69" text-anchor="middle" fill="#8b7e9d">?</text>'
        if condition=='after':
            base+='<path d="m239 104 6 19 19 6-19 6-6 19-6-19-19-6 19-6ZM426 263l4 12 12 4-12 4-4 12-4-12-12-4 12-4Z" fill="#fff"/>'
        return header+base+'</svg>'
    for kind in ('kitchen','glass','mystery'):
        for state in ('before','after','partial'):
            (ASSETS / f'{kind}-{state}.svg').write_text(scene(kind,state))
    (ASSETS/'icon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect width="512" height="512" rx="112" fill="#173d32"/><path d="m256 93 42 121 121 42-121 42-42 121-42-121L93 256l121-42Z" fill="#d3ef86"/><circle cx="240" cy="246" r="10" fill="#173d32"/><circle cx="282" cy="246" r="10" fill="#173d32"/><path d="M244 276q17 19 34 0" fill="none" stroke="#173d32" stroke-width="9" stroke-linecap="round"/></svg>')
    for size in (192,512):
        im=Image.new('RGB',(size,size),'#173d32');d=ImageDraw.Draw(im);s=size/512
        coords=[(256,93),(298,214),(419,256),(298,298),(256,419),(214,298),(93,256),(214,214)]
        d.polygon([(x*s,y*s) for x,y in coords],fill='#d3ef86')
        for x in (240,282):d.ellipse(((x-10)*s,236*s,(x+10)*s,256*s),fill='#173d32')
        d.arc((241*s,262*s,281*s,292*s),0,180,fill='#173d32',width=max(2,int(9*s)))
        im.save(ASSETS/f'icon-{size}.png',optimize=True)
    shutil.copy(ASSETS/'icon-512.png',ASSETS/'icon-maskable.png')


def main():
    catalog=json.loads((ROOT/'server/catalog.json').read_text())
    (ROOT/'client/catalog.ts').write_text('// Generated from server/catalog.json by scripts/build.py. Do not edit independently.\nnamespace GQ {\n export const catalog = '+json.dumps(catalog,indent=2)+' as const;\n export const products: Product[] = JSON.parse(JSON.stringify(catalog.products));\n}\n')
    local_tsc=ROOT/'node_modules/.bin/tsc'
    tsc=str(local_tsc) if local_tsc.exists() else shutil.which('tsc')
    if not tsc:
        raise SystemExit('TypeScript compiler unavailable. Install build dependencies with npm ci, or run the prebuilt web/ without rebuilding.')
    subprocess.run([tsc,'-p','tsconfig.json'],cwd=ROOT,check=True)
    create_art()
    manifest={"id":"/","name":"GrimeQuest · Small chores, real wins","short_name":"GrimeQuest","description":"Your mess becomes a little monster. Snap, clean, defeat it.","start_url":"/","scope":"/","display":"standalone","background_color":"#f7f8f2","theme_color":"#173d32","lang":"en","icons":[{"src":"assets/icon-192.png","sizes":"192x192","type":"image/png","purpose":"any"},{"src":"assets/icon-512.png","sizes":"512x512","type":"image/png","purpose":"any"},{"src":"assets/icon-maskable.png","sizes":"512x512","type":"image/png","purpose":"maskable"}]}
    (WEB/'manifest.webmanifest').write_text(json.dumps(manifest,indent=2)+'\n')
    files=sorted(p for p in WEB.rglob('*') if p.is_file() and p.name!='sw.js')
    digest=hashlib.sha256(b''.join(p.relative_to(WEB).as_posix().encode()+p.read_bytes() for p in files)).hexdigest()[:16]
    # The recovery page MUST stay outside the service-worker cache, including in
    # older installed versions. It can repair a stale offline shell over HTTPS.
    recovery={'update.html','update.js','update.css'}
    paths=['/']+['/'+p.relative_to(WEB).as_posix() for p in files if p.name not in recovery]
    sw="""// Generated app-shell-only cache. NEVER cache API responses, uploads or photos.
const CACHE = 'grimequest-__DIGEST__';
const PATHS = __PATHS__;
// Uvicorn has a finite 24-connection admission cap. cache.addAll(PATHS)
// burst-loaded 28+ shell assets and caused transient HTTP 503 during PWA
// recovery. Load ONE file at a time and retry a transient failed fetch twice.
async function precacheShell() {
  const cache = await caches.open(CACHE);
  try {
    for (const path of PATHS) {
      let failure = null;
      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          await cache.add(path);
          failure = null;
          break;
        } catch (error) {
          failure = error;
          if (attempt < 2) await new Promise(resolve => setTimeout(resolve, 300 * (attempt + 1)));
        }
      }
      if (failure) throw failure;
    }
    // Only a *complete* shell can replace the old active worker.
    await self.skipWaiting();
  } catch (error) {
    // A failed installation must not leave a corrupt partial new cache.
    // Previous complete caches, local inventory and journal are untouched.
    await caches.delete(CACHE);
    throw error;
  }
}
self.addEventListener('install', event => {
  event.waitUntil(precacheShell());
});
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'GRIMEQUEST_ACTIVATE_UPDATE') {
    event.waitUntil(self.skipWaiting());
  }
});
self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k.startsWith('grimequest-') && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (event.request.method !== 'GET' || url.origin !== self.location.origin || url.search || !PATHS.includes(url.pathname) || url.pathname.startsWith('/api/')) return;
  event.respondWith(caches.open(CACHE).then(cache => cache.match(event.request)).then(cached => cached || fetch(event.request)));
});
""".replace('__DIGEST__',digest).replace('__PATHS__',json.dumps(paths))
    (WEB/'sw.js').write_text(sw)
    # Single file for a double-click walkthrough. It intentionally has no live API.
    html=(WEB/'index.html').read_text();js=(WEB/'app.js').read_text();css=(WEB/'styles.css').read_text()
    for asset in ASSETS.glob('*.svg'):
        data='data:image/svg+xml;base64,'+base64.b64encode(asset.read_bytes()).decode()
        js=js.replace('assets/'+asset.name,data)
    html=html.replace('<link rel="stylesheet" href="styles.css">','<style>'+css+'</style>')
    # Inline the public-game skin in the standalone artifact and browser harness too.
    html=html.replace('<link rel="stylesheet" href="game.css">','<style>'+(WEB/'game.css').read_text()+'</style>')
    html=html.replace('<script defer src="vendor/qr-creator.js"></script>','').replace('<script defer src="vendor/zxing-0.21.3.min.js"></script>','').replace('<script defer src="install.js"></script>','').replace('<script defer src="update-client.js"></script>','')
    html=html.replace('<script defer src="app.js"></script>','<script>'+js.replace('</script','<\\/script')+'</script>')
    html='\n'.join(line for line in html.splitlines() if '<link rel="manifest"' not in line and '<link rel="icon"' not in line and '<link rel="apple-touch-icon"' not in line)
    (ROOT/'preview.html').write_text(html)
    print(f'Built {len(files)+1} web files; cache revision {digest}; standalone preview ready.')

if __name__=='__main__':main()
