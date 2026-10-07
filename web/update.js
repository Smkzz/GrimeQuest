/* One-click same-origin repair for stale installed PWAs. No localStorage writes. */
(() => {
  'use strict';
  const button = document.getElementById('refresh-now');
  const status = document.getElementById('refresh-status');
  if (!button || !status) return;
  button.addEventListener('click', async () => {
    if (!navigator.onLine) {
      status.textContent = 'Connect to the internet before refreshing the app.';
      return;
    }
    button.disabled = true;
    status.textContent = 'Updating the app files. Your saved inventory and journal will stay.';
    try {
      // Never touch app data. Unregister only the service worker scoped to the
      // current application root, not unrelated browser registrations.
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.getRegistration('/');
        if (registration && registration.scope === new URL('/', location.origin).href) {
          await registration.unregister();
        }
      }
      if ('caches' in window) {
        const names = await caches.keys();
        await Promise.all(names
          .filter(name => name.startsWith('grimequest-'))
          .map(name => caches.delete(name)));
      }
      // The old worker intentionally ignores query-bearing GET navigation.
      // Once unregistered, the next page also loads all app assets from network.
      window.location.replace('/?app_refresh=' + Date.now());
    } catch (_) {
      status.textContent = 'Could not refresh the app. Check your connection and try again; no saved game data was deleted.';
      button.disabled = false;
    }
  });
})();
