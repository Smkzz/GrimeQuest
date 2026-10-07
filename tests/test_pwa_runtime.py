"""Actual localhost-origin PWA smoke: HTTP, service worker, offline shell and legal pages."""
import os
from pathlib import Path
import socket
import subprocess
import time
import urllib.request

import pytest
from playwright.sync_api import sync_playwright, expect, Error as PlaywrightError

ROOT=Path(__file__).resolve().parents[1]


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def wait_ready(url, timeout=10):
    deadline=time.time()+timeout
    last=None
    while time.time()<deadline:
        try:
            with urllib.request.urlopen(url+'/api/health',timeout=1) as r:
                if r.status==200:return
        except Exception as exc:last=exc
        time.sleep(.1)
    raise AssertionError(f'local server did not become ready: {last}')


def test_real_origin_service_worker_and_offline_shell():
    port=free_port();base=f'http://127.0.0.1:{port}'
    env={**os.environ,'PORT':str(port)}
    process=subprocess.Popen([os.environ.get('PYTHON','python'),'run.py','--host','127.0.0.1'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_ready(base)
        with sync_playwright() as p:
            executable=os.environ.get('GQ_CHROMIUM_EXECUTABLE','/usr/bin/chromium')
            args={'executable_path':executable} if Path(executable).exists() else {}
            browser=p.chromium.launch(headless=True,args=['--no-sandbox'],**args)
            context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
            page=context.new_page()
            try:
                page.goto(base+'/',wait_until='networkidle')
            except PlaywrightError as exc:
                if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(exc):
                    pytest.skip('This execution environment blocks browser navigation to localhost; HTTP-origin checks still run separately.')
                raise
            expect(page.locator('h1')).to_contain_text('A little mess.')
            manifest=page.evaluate("fetch('/manifest.webmanifest').then(r=>r.json())")
            assert manifest['display']=='standalone' and any(i['sizes']=='512x512' for i in manifest['icons'])
            page.evaluate("navigator.serviceWorker.ready.then(r=>!!r.active)")
            page.wait_for_function("navigator.serviceWorker.controller !== null")
            cached=page.evaluate("caches.keys().then(async ks=>{const c=await caches.open(ks.find(k=>k.startsWith('grimequest-')));return (await c.keys()).map(r=>new URL(r.url).pathname)})")
            assert '/' in cached and '/privacy.html' in cached and '/safety.html' in cached
            assert '/vendor/qr-creator.js' in cached and '/install.js' in cached
            assert '/update-client.js' in cached
            assert not any(p in cached for p in ['/update.html','/update.js','/update.css'])
            context.set_offline(True)
            page.reload(wait_until='domcontentloaded')
            expect(page.locator('h1')).to_contain_text('A little mess.')
            page.goto(base+'/privacy.html',wait_until='domcontentloaded')
            expect(page.locator('h1')).to_contain_text('Photos are for the quest')
            context.set_offline(False)
            browser.close()
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill()


def test_real_http_origin_exposes_complete_pwa_shell():
    import json
    port=free_port();base=f'http://127.0.0.1:{port}'
    env={**os.environ,'PORT':str(port)}
    process=subprocess.Popen([os.environ.get('PYTHON','python'),'run.py','--host','127.0.0.1'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        wait_ready(base)
        for path in ['/', '/app.js', '/install.js', '/update-client.js', '/update.html', '/update.js', '/update.css', '/vendor/qr-creator.js', '/styles.css', '/manifest.webmanifest', '/sw.js', '/privacy.html', '/safety.html', '/robots.txt']:
            with urllib.request.urlopen(base+path,timeout=2) as r:
                assert r.status==200, path
                body=r.read()
                assert body, path
                if path=='/':
                    assert 'frame-ancestors' in r.headers['content-security-policy']
                    assert r.headers['cross-origin-opener-policy']=='same-origin'
                if path in ('/update.html', '/update.js', '/update.css'):
                    assert r.headers['cache-control']=='no-store'
        with urllib.request.urlopen(base+'/manifest.webmanifest',timeout=2) as r:
            manifest=json.loads(r.read())
        assert manifest['display']=='standalone' and manifest['scope']=='/'
        sw=urllib.request.urlopen(base+'/sw.js',timeout=2).read().decode()
        assert '/privacy.html' in sw and '/safety.html' in sw and '/api/' in sw
        assert '/update-client.js' in sw and 'self.skipWaiting()' in sw
        assert all(p not in sw for p in ('"/update.html"','"/update.js"','"/update.css"'))
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill()
