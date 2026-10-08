"""Desktop-to-mobile QR handoff and phone PWA install prompt, on a real HTTP origin."""
import os
from pathlib import Path
import subprocess
import pytest
from playwright.sync_api import sync_playwright, expect, Error as PlaywrightError
from test_pwa_runtime import free_port, wait_ready, ROOT


@pytest.fixture(scope='module')
def origin():
    port = free_port()
    base = f'http://127.0.0.1:{port}'
    proc = subprocess.Popen(
        [os.environ.get('PYTHON', 'python'), 'run.py', '--host', '127.0.0.1'],
        cwd=ROOT, env={**os.environ, 'PORT': str(port)},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        wait_ready(base)
        yield base
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill()


def open_or_skip(page, url):
    try:
        page.goto(url, wait_until='networkidle')
    except PlaywrightError as exc:
        if 'ERR_BLOCKED_BY_ADMINISTRATOR' in str(exc):
            pytest.skip('This environment forbids localhost navigation; installation requires an origin.')
        raise


def test_desktop_shows_self_hosted_usable_qr_with_desktop_escape(origin):
    with sync_playwright() as p:
        executable = os.environ.get('GQ_CHROMIUM_EXECUTABLE', '/usr/bin/chromium')
        opts = {'executable_path': executable} if Path(executable).exists() else {}
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **opts)
        context = browser.new_context(viewport={'width': 1280, 'height': 900})
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        open_or_skip(page, origin + '/')
        # A judge can play immediately; installation handoff is opt-in.
        expect(page.locator('#install-gate')).to_be_hidden()
        expect(page.locator('#app h1')).to_contain_text('A little mess.')
        assert not page.locator('#app').evaluate('(el) => el.inert')
        page.locator('[data-action="show-install"]').click()
        expect(page.locator('#install-gate')).to_be_visible()
        expect(page.locator('#install-qr canvas')).to_be_visible()
        assert page.locator('#app').evaluate('(el) => el.inert')
        assert page.locator('#install-link').get_attribute('href') == origin + '/'
        assert page.locator('#install-qr canvas').evaluate(
            '(c) => c.width === 280 && c.height === 280 && '
            'c.getContext("2d").getImageData(0,0,c.width,c.height).data.some((v,i) => i%4===0 && v<128)'
        )
        page.locator('#install-desktop').click()
        expect(page.locator('#install-gate')).to_be_hidden()
        expect(page.locator('#app h1')).to_contain_text('A little mess.')
        assert not page.locator('#app').evaluate('(el) => el.inert')
        page.reload()
        expect(page.locator('#install-gate')).to_be_hidden()
        assert not errors
        context.close()
        browser.close()


def test_iphone_uses_safari_homescreen_guidance_and_preserves_game(origin):
    with sync_playwright() as p:
        executable = os.environ.get('GQ_CHROMIUM_EXECUTABLE', '/usr/bin/chromium')
        opts = {'executable_path': executable} if Path(executable).exists() else {}
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **opts)
        context = browser.new_context(
            viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
        )
        page = context.new_page()
        open_or_skip(page, origin + '/')
        expect(page.locator('#install-gate')).to_be_hidden()
        expect(page.locator('#install-tip')).to_be_visible()
        expect(page.locator('#app h1')).to_contain_text('A little mess.')
        page.locator('#install-cta').click()
        expect(page.locator('#install-steps')).to_contain_text('Add to Home Screen')
        expect(page.locator('#install-steps')).to_contain_text('Open as Web App')
        page.locator('#install-dismiss').click()
        expect(page.locator('#install-tip')).to_be_hidden()
        page.reload()
        expect(page.locator('#install-tip')).to_be_hidden()
        context.close()
        browser.close()


def test_android_receives_browser_install_instructions(origin):
    with sync_playwright() as p:
        executable = os.environ.get('GQ_CHROMIUM_EXECUTABLE', '/usr/bin/chromium')
        opts = {'executable_path': executable} if Path(executable).exists() else {}
        browser = p.chromium.launch(headless=True, args=['--no-sandbox'], **opts)
        context = browser.new_context(
            viewport={'width': 412, 'height': 915}, is_mobile=True, has_touch=True,
            user_agent='Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36'
        )
        page = context.new_page()
        open_or_skip(page, origin + '/')
        expect(page.locator('#install-gate')).to_be_hidden()
        page.locator('#install-cta').click()
        expect(page.locator('#install-steps')).to_contain_text('Install app')
        assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
        context.close()
        browser.close()
