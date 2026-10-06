# Prototype privacy boundaries

The source application contains no analytics, ads, tracking pixels or account SDKs. This describes the included code, not a complete legal policy for a future public service.

**On this browser:** inventory names/notes, up to 200 comparison records, mode-specific XP inputs and an interrupted-task warning are stored locally. Completion records may include signed result receipts and image digests, but never the photo bytes. The private application access code is in tab-session storage, separate from provider credentials. Exported journals do not contain access codes or photos. A shared or compromised device can expose local records. Private-browsing or storage restrictions may prevent persistence.

**In memory:** selected photos remain in the current page until the task is finished/abandoned, the selection is replaced, local data is deleted, or the page closes/reloads. Camera streams stop on navigation, visibility loss and page exit. Front/back product photos are cleared after saving/abandoning the product workflow. Closing a tab does not delete data already sent to a provider.

**At the server:** live images are bounded, decoded and re-encoded in memory, not written to the filesystem by application code. EXIF metadata is removed before provider submission. The application disables request access logs through `run.py`; it does not log image bodies, labels, keys or model text. Hosting infrastructure, proxies or a debugger could add logs; operators must verify their configuration. Temporary result caching contains bounded receipt metadata, not photos. Process restarts discard it.

**At the selected provider:** explicitly approved live requests send the normalized photo(s) via the operator's configured endpoint. Provider retention, use and regional-processing policies are external to this application. The UI shows the configured provider hostname. Read the actual provider terms before enabling live use. EXIF removal does not remove a face, address or private document visible in pixels. No automatic redaction is promised.

Practice illustrations never need a provider call. The service worker caches only named public app-shell assets, not images supplied by a person, labels, API responses or secrets.

Deletion in Settings removes the app's local history, inventory and tab access code. It does not recall provider submissions, delete browser downloads or remove physical cleaner residues. A public service would need its own jurisdiction-appropriate policies, operator identity, retention controls and consent review; those are not supplied by this prototype.
