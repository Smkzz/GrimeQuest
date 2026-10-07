"""Local release checks. No network, paid model, or external account actions."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]

def digest(paths):
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def main():
    expected=json.loads((ROOT/'package.json').read_text())['devDependencies']['typescript']
    compiler=ROOT/'node_modules'/'typescript'/'bin'/'tsc'
    cmd=['node',str(compiler)] if compiler.exists() else ['tsc']
    version=subprocess.check_output([*cmd,'--version'],text=True).strip()
    if version != 'Version '+expected:raise SystemExit('Build requires the pinned TypeScript '+expected)
    paths=sorted(p for p in (ROOT/'web').rglob('*') if p.is_file())+[ROOT/'client/catalog.ts',ROOT/'preview.html']
    before=digest(paths)
    subprocess.run([sys.executable,str(ROOT/'scripts/build.py')],cwd=ROOT,check=True)
    after=digest(paths)
    if before!=after:raise SystemExit('Generated output drifted; review and repeat the check.')
    manifest=json.loads((ROOT/'web/manifest.webmanifest').read_text())
    assert manifest['display']=='standalone' and manifest['start_url']=='/'
    for icon in manifest['icons']:assert (ROOT/'web'/icon['src'].lstrip('/')).is_file()
    sw=(ROOT/'web/sw.js').read_text()
    assert 'skipWaiting(' not in sw and '/api/' in sw
    assert 'addAll(PATHS)' in sw
    runtime=list((ROOT/'web').rglob('*'))
    forbidden=['GQ_PROVIDER_KEY=sk-','sk-proj-','-----BEGIN PRIVATE KEY-----']
    for path in runtime:
        if path.is_file() and path.suffix in {'.js','.html','.css','.json'}:
            text=path.read_text()
            assert not any(secret in text for secret in forbidden),path
    # No vendor libraries, fonts, secrets or household photos belong in the web bundle.
    assert not list((ROOT/'web').rglob('*.ttf')) and not list((ROOT/'web').rglob('*.woff*'))
    counts={'web_files':len([p for p in runtime if p.is_file()]),'runtime_js_bytes':(ROOT/'web/app.js').stat().st_size,
            'standalone_preview_bytes':(ROOT/'preview.html').stat().st_size,
            'generated_files_byte_identical_after_rebuild':True,'compiler':version,
            'provider_calls':0,'external_ci_executed':False,'dependency_advisory_scan':'not_run_by_this_script; see docs/TEST_REPORT.md'}
    (ROOT/'evidence').mkdir(exist_ok=True)
    (ROOT/'evidence/build-check.json').write_text(json.dumps(counts,indent=2)+'\n')
    print(json.dumps(counts,indent=2))

if __name__=='__main__':main()
