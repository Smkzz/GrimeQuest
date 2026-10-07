/* GrimeQuest SW version guard. Never forces reload while a quest is open. */
(() => {
  'use strict';
  if (!('serviceWorker' in navigator) || !window.isSecureContext || location.protocol === 'file:') return;
  const banner = document.getElementById('app-update-banner');
  const updateButton = document.getElementById('app-update-now');
  const laterButton = document.getElementById('app-update-later');
  const hadController = Boolean(navigator.serviceWorker.controller);
  let dismissed = false;

  const show = () => {
    if (!dismissed && banner && hadController) banner.hidden = false;
  };
  updateButton?.addEventListener('click', () => { window.location.assign('/update.html'); });
  laterButton?.addEventListener('click', () => {
    dismissed = true;
    if (banner) banner.hidden = true;
  });
  navigator.serviceWorker.addEventListener('controllerchange', show);

  (async () => {
    try {
      const registration = await navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' });
      if (registration.waiting) show();
      registration.addEventListener('updatefound', () => {
        const installing = registration.installing;
        installing?.addEventListener('statechange', () => {
          if (installing.state === 'installed' && registration.waiting) show();
          if (installing.state === 'activated') show();
        });
      });
      // Registration itself does not always check for an update promptly on
      // long-lived iPhone Home Screen processes; request a fresh check on boot.
      await registration.update();
    } catch (_) {
      // Network loss must not block the offline practice game or local journal.
    }
  })();
})();
