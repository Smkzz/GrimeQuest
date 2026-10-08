/* GrimeQuest device handoff. Local-only QR generation; no tracking or external QR services. */
(() => {
  'use strict';

  const gate = document.getElementById('install-gate');
  const tip = document.getElementById('install-tip');
  const app = document.getElementById('app');
  if (!gate || !tip || !app) return;

  const readonlyStore = (name) => {
    try { return sessionStorage.getItem(name) === '1'; } catch (_) { return false; }
  };
  const saveFlag = (name) => {
    try { sessionStorage.setItem(name, '1'); } catch (_) { /* Optional storage. */ }
  };
  const standalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
  const ua = navigator.userAgent || '';
  const phoneOrTablet = /Android|iPad|iPhone|iPod|Mobile|Tablet/i.test(ua) ||
    navigator.userAgentData?.mobile === true ||
    (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
  const webOrigin = location.protocol === 'https:' || location.protocol === 'http:';
  const phoneUrl = webOrigin ? new URL('/', location.origin).href : '';
  let deferredInstall = null;

  function hideGate() {
    gate.hidden = true;
    app.inert = false;
    app.removeAttribute('aria-hidden');
    saveFlag('gq_desktop_play');
    document.getElementById('install-desktop')?.blur();
    app.querySelector('h1')?.focus({ preventScroll: true });
  }

  function presentDesktop() {
    const link = document.getElementById('install-link');
    if (link) { link.href = phoneUrl; link.textContent = phoneUrl; }
    const qr = document.getElementById('install-qr');
    try {
      if (qr && window.QrCreator?.render) {
        qr.replaceChildren();
        window.QrCreator.render({
          text: phoneUrl, size: 280, quiet: 4, radius: 0,
          ecLevel: 'M', fill: '#173d32', background: '#ffffff'
        }, qr);
        qr.querySelector('canvas')?.setAttribute('aria-hidden', 'true');
      } else if (qr) qr.textContent = 'Use the link below to open GrimeQuest on your phone.';
    } catch (_) {
      if (qr) qr.textContent = 'QR code unavailable. Use the link below instead.';
    }
    app.inert = true;
    app.setAttribute('aria-hidden', 'true');
    gate.hidden = false;
    document.getElementById('install-heading')?.setAttribute('tabindex', '-1');
    document.getElementById('install-heading')?.focus({ preventScroll: true });
    const escapeButton = document.getElementById('install-desktop');
    if (escapeButton) escapeButton.onclick = hideGate;
    const copyButton = document.getElementById('install-copy');
    if (copyButton) copyButton.onclick = async () => {
      const status = document.getElementById('install-copy-status');
      try {
        await navigator.clipboard.writeText(phoneUrl);
        if (status) status.textContent = 'Link copied.';
      } catch (_) {
        if (status) status.textContent = 'Select and copy the address above.';
      }
    };
  }

  function revealPhoneSteps() {
    const steps = document.getElementById('install-steps');
    if (!steps) return;
    const iphone = /iPad|iPhone|iPod/i.test(ua) ||
      (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
    if (iphone) {
      steps.textContent = /Safari/i.test(ua) && !/CriOS|FxiOS|EdgiOS|OPiOS/i.test(ua)
        ? 'In Safari, tap Share (or Page Menu → Share), choose Add to Home Screen, leave Open as Web App on, then tap Add.'
        : 'Open this page in Safari, tap Share, then Add to Home Screen. Leave Open as Web App on and tap Add.';
    } else if (/Android/i.test(ua)) {
      steps.textContent = 'In Chrome, open the three-dot menu and choose Install app or Add to Home screen, then confirm.';
    } else {
      steps.textContent = 'Open your browser menu and choose Install app or Add to Home Screen if available.';
    }
    steps.hidden = false;
  }

  function hideTip() {
    tip.hidden = true;
    saveFlag('gq_install_tip_dismissed');
  }

  let phonePresented = false;
  function presentPhone(force = false) {
    if (!force && readonlyStore('gq_install_tip_dismissed')) return;
    tip.hidden = false;
    if (phonePresented) return;
    phonePresented = true;
    const cta = document.getElementById('install-cta');
    const dismiss = document.getElementById('install-dismiss');
    dismiss?.addEventListener('click', hideTip);
    cta?.addEventListener('click', async () => {
      if (!deferredInstall) { revealPhoneSteps(); return; }
      const prompt = deferredInstall;
      deferredInstall = null;
      try {
        await prompt.prompt();
        const choice = await prompt.userChoice;
        if (choice?.outcome !== 'accepted') revealPhoneSteps();
      } catch (_) { revealPhoneSteps(); }
      if (cta) cta.textContent = 'How to install';
    });
    window.addEventListener('beforeinstallprompt', event => {
      event.preventDefault();
      deferredInstall = event;
      if (cta) cta.textContent = 'Install GrimeQuest';
    });
    window.addEventListener('appinstalled', () => {
      tip.hidden = true;
      saveFlag('gq_install_tip_dismissed');
    });
  }

  // Do not block the desktop game with an installation gate on first load.
  // Judges and players must be able to start a quest immediately on any device.
  window.addEventListener('grimequest:show-install', () => {
    if (!webOrigin) return;
    if (phoneOrTablet) {
      presentPhone(true);
      revealPhoneSteps();
    } else {
      presentDesktop();
    }
  });
  // Never obscure the first camera-quest CTA with an unsolicited install card.
  // The optional Install / share control opens this guide on demand.
})();