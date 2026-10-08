# GrimeQuest

**Small chores. Real wins.** A camera-first cleaning quest PWA.

**Zero-setup complete camera play:** The default guided mode lets anyone choose a before photo, describe a real glass/glazed-ceramic cleaning target they have independently verified, select their own instruction-checked cleaning method, complete five safety confirmations, take an after photo and self-report what visibly changed. It uses zero AI calls, uploads no photographs and requires no account, access code, server settings or API payment. Guided XP/history are **clearly marked self-reported and separate** from simulated practice and model-observed AI results. A result cannot be claimed from the exact same before/after photo. This is a *gameplay fallback*, not AI verification or chemical-safety certification. All use of products remains governed by their actual label and surface care; unsupported/damaged/uncertain targets must not be treated as safe. AI-powered vision remains a separately consented, cost-controlled optional beta when enabled by the operator.

**Build guard:** Production's existing Railway frontend build stage now runs all no-network Node client tests and byte-identical generated-PWA verification before the final runtime image can deploy; tests and Node tooling are NOT copied to the runtime image. Manual GitHub Actions remain untriggered.

**Why 'Read both labels' can be unavailable:** Photos are processed locally even in Practice mode. This does **not** mean the hosted AI label reader is available. The page now explains whether it is checking the server, unable to connect, server-disabled, missing private test access, in Practice mode, or missing one of the photos. Public production AI has not been activated; the ZDR-only three-request exploratory test did not qualify a public release. If private AI becomes configured and authorized, a tester must enter a private code (when required), explicitly switch to live mode, select both photos and separately consent before any API call. Users can always manually record the label as unreviewed; no scanning result grants chemical safety permission.

**Installed PWA updates and stale-cache repair:** The old cache-first offline worker could continue serving the 12 MP photo rejection after newer code was deployed. The new service worker fully precaches its replacement before activating (without automatically reloading an active cleaning session), checks for updates on boot, and offers an update notice on already-updated clients. **Settings → Refresh or repair this installation** opens /update.html, a separate same-origin, network-only maintenance page excluded from the service-worker cache. Its explicitly activated refresh unregisters only the GrimeQuest root worker, deletes only `grimequest-*` offline shell caches and navigates via a query URL that older workers bypass. No localStorage, sessionStorage, photos, catalog rules, provider credentials, or Home Screen icon are deleted. An ongoing in-memory photo quest may be lost: finish the actual cleaning task before updating. Safari Home Screen apps may have storage isolated from Safari tabs, so recovery should be done inside the installed app whenever possible.

**Install from a computer:** Visit the HTTPS production URL on a desktop browser. The page displays a locally generated QR code encoding that same origin (no third-party QR service, tracking, or phone-OS guessing by screen width). Scan with your phone camera, tap the link, then follow the mobile install prompt. You can still choose **Continue in desktop browser**. On iPhone/iPad use Safari → Share → Add to Home Screen → Open as Web App → Add; on Android Chrome use the browser's Install app / Add to Home screen option. QR scanning opens the site; **it never silently installs an app**. The existing manifest, Home Screen icons and allowlisted offline service worker remain in use. Mobile users can dismiss the installation hint. Live AI stays disabled for public users.


Identify one visible mess, confirm its material, choose a product from your own inventory, do the real cleaning, and compare the result. The useful core is product matching; the game adds a reason to start and finish.

**v0.1.0 is a working, externally clean-room-qualified prototype, not a publicly qualified chemical-advice service.** The shipped default is an explicitly simulated practice mode. The live application protocol is qualified with deterministic observations, but no real vision model or physical cleaning trial has yet passed the release gate. See [test evidence](docs/TEST_REPORT.md) and [release gates](docs/RELEASE_GATES.md).


## Zero-setup real camera play

1. Open GrimeQuest on a phone and choose **Start camera quest**. No registration, API key or code.
2. Take a before photo, confirm the actual surface and visible soil, and choose a method you independently know is permitted. The app is not certifying any unknown product.
3. Review the five care checks, perform the actual task following the current product/surface instructions, then take a comparable after photo when dry.
4. Report what you can see. Results appear as **SELF-REPORTED**, earn only guided XP, and are not presented as model verification or chemical-safety approval. Identical before/after photos are rejected for clear results.
5. If the operator has activated and verified the fixed ZDR model within its preflight and call budgets, the server automatically offers consent-based **AI Beta**. Players are never shown server configuration. If AI Beta is unavailable or rate-limited, the real camera quest still works.

## Try it immediately

The full repo-backed application is deployed over HTTPS at:

`https://grimequest-web-production.up.railway.app/`

Railway builds the PWA from source in a digest-pinned multi-stage Docker image, runs one FastAPI replica in Amsterdam, enforces a 0.5 vCPU / 0.5 GB per-replica ceiling, and checks `/api/health`. The currently hosted release is healthy and live AI is intentionally disabled after hosted protocol qualification. Practice mode is available without an account or API key, and its illustrated outcomes are **not AI analyses or physical cleaning evidence**.

Generated frontend bundles are intentionally not committed. `python scripts/build.py` compiles the TypeScript, generates the PWA assets/service worker and writes `preview.html` for an optional double-click walkthrough.

## Run from this source folder

Requirements: Python 3.11+ (tested with 3.13.5) and Node 22+. Keep `run.py`, `server/`, `client/`, `scripts/` and `web/` together. This is distributed as a source application, not a standalone Python wheel.

**Windows PowerShell**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
npm ci --ignore-scripts
.\.venv\Scripts\python.exe scripts/build.py
.\.venv\Scripts\python.exe run.py
```

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
npm ci --ignore-scripts
.venv/bin/python scripts/build.py
.venv/bin/python run.py
```

Open `http://127.0.0.1:8000` on the same computer. Stop with Ctrl+C. Practice mode works immediately. Server startup makes no AI call. Network package installation was not available in the build environment; the tests used installed versions recorded in the lock files.

A phone's `localhost` is the phone, not your computer. Real phone-camera use needs a reachable HTTPS origin and a properly configured reverse proxy; do not simply expose an unauthenticated development server. Camera permission and PWA installation are browser-dependent ([MDN camera guidance](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia), [PWA installation](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Making_PWAs_installable)).

## What is implemented

| Area | Current behavior |
| --- | --- |
| Mobile interface | Responsive quest, inventory, care-check, capture, comparison, journal and settings screens |
| Practice mode | Three explicitly illustrated scenarios: grease, fingerprints, and an unsupported material |
| Camera and photos | Permission-on-click, native-resolution JPEG/PNG/WebP and Safari 17+ HEIC/HEIF file input (24/48+ MP accepted); browser-assisted downsampling on supported devices followed by local 1600px-long-edge JPEG conversion with adaptive compression below server's 2 MB upload limit, 100 MB source file guard, HEIC fallback guidance, track cleanup and explicit per-request upload consent |
| Inventory | Local manual product entry even while AI is off; explicit private/public live gate for front/back label reading; locally saved unreviewed notes; manually linked exact catalog variants |
| Matching | Separate deterministic policy with exclusions, hazard gates, five owner confirmations and catalog expiry |
| Comparison | Clear / partial / unverifiable; one 300-XP clear per encounter; practice/live separation |
| API | Strict schemas, bounded images and provider calls, signed workflow receipts, duplicate/concurrent request handling |
| Persistence | Latest 200 comparison records, up to 40 products, interrupted-task warning; no photo journal |
| PWA | Manifest, icons and an allowlisted static-shell service worker; no API/photo caching |

## Configure live analysis deliberately

**Budget/ZDR qualification update (2026-10-08):** Paid OpenRouter evaluation now fails closed unless a dedicated key has a provider-enforced, **non-resetting ≤US$0.50** total cap including BYOK. OpenRouter image calls require `provider.zdr=true`, `provider.data_collection="deny"`, and `require_parameters=true`. The existing shared key's cap was too high; **no paid inference was made**. See [bounded paid-vision runbook](docs/PAID_VISION_PRECHECK.md).

Live mode requires a **vision-capable Chat Completions-compatible endpoint** supporting image inputs and strict JSON-schema responses. Endpoint/model compatibility has not been established against a real service in this release. There is no hard-coded paid model and no automatic fallback to a simulation.

The adapter posts to `<GQ_PROVIDER_BASE>/chat/completions`, requests strict JSON-schema structured output, caps output at 1,800 tokens, and validates the response again against strict Pydantic schemas. On OpenRouter it also requires routing only to endpoints that support every requested parameter. Provider-specific unsupported parameters, refusals or incomplete output fail without issuing a cleaning result.

Create a private code:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Set these **server-side environment variables**, then restart:

```text
GQ_PROVIDER_BASE=https://your-selected-provider.example/v1
GQ_PROVIDER_MODEL=your-tested-vision-model
GQ_PROVIDER_KEY=your-provider-key
GQ_ACCESS_CODE=your-random-private-code-at-least-24-characters
GQ_TICKET_SECRET=your-random-persistent-signing-secret-at-least-32-characters
GQ_MAX_CALLS_HOUR=40
GQ_MAX_CALLS_DAY=200
# Optional public demo; default off. See below.
GQ_PUBLIC_LIVE=0
```

On PowerShell, use `$env:GQ_PROVIDER_BASE = '...'`; on a POSIX shell use `export GQ_PROVIDER_BASE='...'`. `.env.example` documents settings, but the application intentionally does **not** auto-load `.env` files. Never commit credentials.

For an externally hosted app also set `GQ_APP_ORIGIN=https://your-app.example`. Use one server process. A deliberately enabled, operator-managed loopback provider may use HTTP only with `GQ_ALLOW_LOCAL_PROVIDER=1`; it must still support the required vision protocol. Do not assume a local model will be accurate enough.

In private-preview mode, open **Settings → save the private access code → Live camera**. Provider keys never belong in the frontend. Provider fees and data-retention terms may apply; call-count limits are not dollar budgets. A normal successful encounter needs target analysis plus a comparison. Reading product labels is a separate model call. No request is retried automatically.

### Public demo mode

For a hackathon/judging deployment, `GQ_PUBLIC_LIVE=1` removes the shared access-code prompt while keeping same-origin enforcement and the server's concurrency/hour/day ceilings. It is deliberately opt-in and fails configuration unless a persistent `GQ_TICKET_SECRET` exists and `GQ_MAX_CALLS_DAY <= 200`. Keep it off for private previews. If using a provider with a 50-request/day free allowance, use a lower app ceiling such as `GQ_MAX_CALLS_DAY=45` so GrimeQuest stops before the provider quota.

## Important scope boundaries

The reviewed reference catalog now contains **five exact consumer variants**: two UK Method products plus three current Finland-market Kiilto 600 ml fragrance-free sprays (Ikkuna, Koti and Keittiö). Every entry is source-linked to the manufacturer's current product guidance and enabled only for a narrower subset of glass/glazed-ceramic jobs. These are not buying recommendations or safety certification. A similar scent, package size, regional variant or bottle appearance is not an exact match; do not buy a product merely to use the prototype.

**Scanned products stay unreviewed.** OCR/vision text cannot add compatibility permissions. Unknown materials, limescale, hobs, steel, stone, wood, hazardous/unknown chemicals, hot/electrical targets, mould and body fluids are outside this prototype's enabled scope. Actual product labels and surface-care guidance always take precedence. The source review date is not an independent expert approval. Suggestions expire after the catalog validity date unless reviewed.

The model observes appearance. It cannot establish microbiological cleanliness, identify hidden chemical residues, certify material composition, or prove who performed a task. HMAC receipts bind a software workflow, not physical reality. An unsafe selection is blocked in the application; software cannot physically prevent misuse. [Read the safety design](docs/SAFETY.md).

## Build and test

Development needs Node 22+, TypeScript 5.8.3 and the Python test dependencies. The frontend has **zero runtime npm dependencies**.

```bash
python -m pip install -r requirements-dev.lock
npm ci --ignore-scripts
python scripts/build.py
npm run typecheck
npm test
python -m playwright install chromium
python -m pytest --cov=server --cov-report=term-missing
python scripts/verify_build.py
```

`GQ_CHROMIUM_EXECUTABLE` can name an existing Chromium executable. Tests use a deterministic catalog-valid fixture date. The normal browser suite covers desktop and phone layouts, while `tests/test_pwa_runtime.py` starts the real server and exercises the real browser origin, service worker, offline app shell and legal routes.

The latest Railway clean-room qualification runs on **Python 3.13.16 + Node 22.23.3 + Chromium** and records **413 Python/API/browser/evaluation tests + 36 client tests = 449/449 passes, zero skips or warnings**, **97.76% combined Python line/branch coverage**, **1,680 client/server policy combinations agreeing**, with the vision-release evaluator additionally rejecting surface–soil pairs not covered by any reviewed product, strict TypeScript 5.8.3 compilation, zero npm audit findings during clean install, and a byte-identical PWA rebuild. A separate OSV querybatch audit checked **32 exact pinned Python runtime/test packages plus TypeScript entries in total and found 0 known vulnerabilities / 0 errors** after catching and fixing an earlier pytest advisory. A subsequent auditable Trivy whole-rootfs scan of the **remediated equivalent runtime** found zero HIGH/CRITICAL issues after removing unused Python tooling. The updated production Dockerfile passed an isolated Railway canary build and healthcheck. An exact final registry-image attestation and independent review remain separate launch steps.

## Architecture and handoff

- [Architecture and tradeoffs](docs/ARCHITECTURE.md)
- [Safety and catalog extension protocol](docs/SAFETY.md)
- [Privacy boundaries](PRIVACY.md)
- [Security model](SECURITY.md)
- [Test report](docs/TEST_REPORT.md)
- [Actual-cleaning demo script](docs/DEMO_SCRIPT.md)
- [Physical iPhone/Android release checklist](docs/PHONE_RELEASE_CHECKLIST.md)
- [Manufacturer-catalog source review (2026-10-08)](docs/PRODUCT_CATALOG_REVIEW_20261008.md)
- [Release checklist and validation plan](docs/RELEASE_GATES.md)
- [Build plan and completed iterations](docs/BUILD_PLAN.md)
- [Hackathon provenance](docs/HACKATHON_PROVENANCE.md)
- [Hosted deployment status](docs/HOSTED_STATUS.md)
- [Vision provider evaluation plan](docs/PROVIDER_EVALUATION.md)
- [Real provider smoke-test results (2026-10-08)](docs/REAL_PROVIDER_SMOKE_20261008.md)
- [Gemini fixed-model ZDR live-image trial, three calls (2026-10-08)](docs/REAL_FIXED_ZDR_TRIAL_20261008.md)
- [Vision provider qualification dataset](eval/README.md)

CI is provided as a **manual-only GitHub Actions workflow**. The source is still hosted in the private GitHub repository `Smkz-Entertainment/GrimeQuest`; normal pushes do not trigger CI. Generated frontend bundles and qualification evidence are ignored by Git and can be regenerated locally; `scripts/package_release.py` includes generated runtime files and available evidence in a release archive.

The repo-backed Python service is deployed successfully on Railway. A temporary deterministic vision fixture and external qualification runner exercised the complete hosted HTTPS live protocol—authentication rejection, target observation, product transcription remaining unreviewed, eligibility/start, signed encounter, comparison, XP and idempotent repeat—then both temporary services were deleted and production was restored to AI-off-by-default. That qualification proves the network/application protocol, **not real model accuracy**. Physical phone/cleaning validation remains outstanding. The repository must still be made public before a hackathon submission that requires open source.

## License

Original application code and original illustrations: MIT. Dependency licenses remain their own. Product names and manufacturer material are third-party identifiers, not an endorsement; see [third-party notices](THIRD_PARTY_NOTICES.md).
