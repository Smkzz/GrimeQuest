# GrimeQuest

**Point. Clean. Score.** A tiny, casual mobile game that turns real-world cleaning into XP.

Play GrimeQuest: **https://grimequest-web-production.up.railway.app/**

## The entire game

1. **Snap the dirt.** Point your camera at one messy spot and take a before photo. You can also choose an existing photo.
2. **Clean it.** Do the real task at your own pace using the proper care instructions you already have. No game timer.
3. **Snap again.** Photograph the same spot, tap **It’s clean!**, and earn **+300 XP**.

That’s it. No registration, product search, cleaner menus, material classification, owner configuration or AI API key. A **My wins** page keeps your local XP and completed quest history. You can keep playing offline after the PWA is installed.

**Truthful outcome:** Points are based on a **player self-report and two photos**, not automatic image recognition, a verified cleaning measurement, germ removal, disinfection or evidence of which product/method was used. Identical before/after photos cannot claim a clear. GrimeQuest never recommends a cleaning chemical.

**Safety:** Read and follow the actual object's care instructions and any cleaning product's current label. Never mix or layer cleaners. Stop if the material, residue, appliance electrical/heat status or appropriate care is unknown. The app is a game, **not chemical or surface compatibility advice**.

## Player privacy

Before/after photos are processed **on the device**, temporarily kept only in tab memory and not uploaded in the casual game. Photos are not stored in the journal. XP/history remain in the browser's local storage, without a user account or analytics. Closing/reloading mid-quest loses unsaved photos; completed wins survive, unless browser storage is cleared. Use **Settings (⋯)** to install/share, inspect policies, repair the PWA or delete local data.

The old barcode, product catalog and optional AI API code remain isolated in the repository for backward-compatibility and tests; **they are not exposed in the public casual experience**. They do not grant cleaning safety permissions. Server-based AI mode is disabled and is **not** necessary for a full game.

## Install and run

GrimeQuest is an installable progressive web app (PWA), playable directly from the HTTPS link above. On iOS Safari choose **Share → Add to Home Screen** (with Open as Web App enabled, when offered), or use **Settings (⋯) → Install / share** for instructions. The first visit is never blocked by a QR code or install prompt. On a computer you can also play immediately or open the optional QR handoff in Settings.

Local developer requirements: Python 3.13+, Node 22+.

```sh
python -m pip install -r requirements-dev.lock
npm ci --ignore-scripts
python scripts/build.py
npm run typecheck
npm test
python -m playwright install chromium
python -m pytest --cov=server --cov-fail-under=90
python run.py --host 127.0.0.1
```

The Docker production build reproduces the PWA shell and runs offline Node client tests, product-provider contract mocks and privacy/policy smoke checks before deployment. `Dockerfile.qualify` runs a separate clean-room Python/Node/Chromium qualification including casual end-to-end and original backend compatibility. No paid AI provider calls are necessary for these tests. GitHub Actions are manual-only to avoid unexpected CI expense.

### Testing and launch evidence

- [Physical device checklist](docs/PHONE_RELEASE_CHECKLIST.md) — real iPhone/iOS camera and installed-PWA acceptance.
- [Release gates](docs/RELEASE_GATES.md), [safety policy](docs/SAFETY.md), [privacy notice](PRIVACY.md) and [third-party notices](THIRD_PARTY_NOTICES.md).
- [Final pre-simplification audit](docs/FINAL_LAUNCH_AUDIT_20261008.md). It covers the older guided/AI/product-menu game and is not evidence for the new casual layout.
- [Demo script](docs/DEMO_SCRIPT.md).

**External acceptance remains essential:** Test the entire before → clean → after → XP → wins loop on an actual iPhone Home Screen app, including photo permissions and a native HEIC picture. Browser automation cannot certify physical camera hardware or whether real-world cleaning occurred.

## Project

This MIT-licensed project was built for an international gamification hackathon. Original code and illustrations are in this repository. It does not operate a shop, chemical-recommendation engine, or public AI verification system.

See [LICENSE](LICENSE).
