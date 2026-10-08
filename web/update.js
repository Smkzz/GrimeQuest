/* Safe GrimeQuest Home Screen refresh: never erase a working offline shell. */
(() => {
  'use strict';
  const button = document.getElementById('refresh-now');
  const status = document.getElementById('refresh-status');
  if (!button || !status) return;

  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const corePaths = ['/', '/app.js', '/styles.css', '/update-client.js'];

  async function latestCacheRevision() {
    // Query-bearing URLs bypass both current and older cache-first workers.
    // A temporary 503 must not cause the current working PWA to be uninstalled.
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const response = await fetch('/sw.js?refresh_check=' + Date.now() + '-' + attempt, {
          method: 'GET',
          cache: 'no-store',
          credentials: 'omit',
          redirect: 'error',
          signal: AbortSignal.timeout(5000)
        });
        if (!response.ok) throw new Error('Service temporarily unavailable');
        const source = await response.text();
        if (source.length > 100_000) throw new Error('Invalid service worker');
        const match = source.match(/const CACHE = '(grimequest-[a-f0-9]{16})';/);
        if (!match) throw new Error('Unexpected service worker version');
        return match[1];
      } catch (_) {
        if (attempt === 2) throw new Error('GrimeQuest server is temporarily unavailable. Your current app is unchanged; try refreshing again shortly.');
        status.textContent = 'Server is briefly busy. Retrying the version check safely…';
        await sleep(650 * (attempt + 1));
      }
    }
    throw new Error('Could not verify the newest app.');
  }

  async function fullyReady(registration, revision) {
    if (!registration.active || registration.active.state !== 'activated' ||
        registration.installing || registration.waiting) return false;
    const available = await caches.keys();
    if (!available.includes(revision)) return false;
    const cache = await caches.open(revision);
    for (const path of corePaths) {
      if (!await cache.match(path)) return false;
    }
    return true;
  }

  button.addEventListener('click', async () => {
    if (!navigator.onLine) {
      status.textContent = 'Connect to the internet before refreshing the app. Your offline copy remains available.';
      return;
    }
    if (!('serviceWorker' in navigator) || !('caches' in window)) {
      status.textContent = 'This browser does not support safe offline updates. Open GrimeQuest normally in your browser; no saved data was changed.';
      return;
    }
    button.disabled = true;
    status.textContent = 'Checking the new version. Your saved inventory and current offline app are safe.';
    try {
      const expected = await latestCacheRevision();
      let registration = await navigator.serviceWorker.getRegistration('/');
      if (!registration) registration = await navigator.serviceWorker.register('/sw.js', { updateViaCache: 'none' });
      else await registration.update();
      // The service worker fetches a COMPLETE shell before it activates. If
      // anything returns HTTP 503, we leave the previous worker and cache alone.
      status.textContent = 'Preparing the updated app. The previous version remains available until it is ready.';
      for (let attempt = 0; attempt < 90; attempt++) {
        if (registration.waiting) {
          registration.waiting.postMessage({ type: 'GRIMEQUEST_ACTIVATE_UPDATE' });
        }
        if (await fullyReady(registration, expected)) {
          status.textContent = 'Updated files ready. Opening GrimeQuest…';
          // The ACTIVE worker serves '/' from the newly completed offline
          // cache, avoiding another potentially overloaded network navigation.
          window.location.replace('/');
          return;
        }
        await sleep(250);
      }
      throw new Error('The updated app could not finish loading. Your previous offline version is preserved. Try again later.');
    } catch (error) {
      status.textContent = error instanceof Error
        ? error.message
        : 'Could not check the new app. Your saved data and offline copy are unchanged.';
      button.disabled = false;
    }
  });
})();