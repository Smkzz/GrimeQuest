# GrimeQuest

**Small chores. Real wins.** A camera-first cleaning quest PWA.

Identify one visible mess, confirm its material, choose a product from your own inventory, do the real cleaning, and compare the result. The useful core is product matching; the game adds a reason to start and finish.

**v0.1.0 is a working, locally tested prototype, not a publicly qualified chemical-advice service.** The shipped default is an explicitly simulated practice mode. The live API and client flow are implemented and tested with injected observations. No real vision provider or physical cleaning trial has been validated for this release. See [test evidence](docs/TEST_REPORT.md) and [release gates](docs/RELEASE_GATES.md).


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
| Camera and photos | Permission-on-click, file fallback, resizing, track cleanup, and explicit per-request upload consent |
| Inventory | Local product notes; front/back label analysis; manually linked exact catalog variants |
| Matching | Separate deterministic policy with exclusions, hazard gates, five owner confirmations and catalog expiry |
| Comparison | Clear / partial / unverifiable; one 300-XP clear per encounter; practice/live separation |
| API | Strict schemas, bounded images and provider calls, signed workflow receipts, duplicate/concurrent request handling |
| Persistence | Latest 200 comparison records, up to 40 products, interrupted-task warning; no photo journal |
| PWA | Manifest, icons and an allowlisted static-shell service worker; no API/photo caching |

## Configure live analysis deliberately

Live mode requires a **vision-capable Chat Completions-compatible endpoint** supporting image inputs and JSON-object responses. Endpoint/model compatibility has not been established against a real service in this release. There is no hard-coded paid model and no automatic fallback to a simulation.

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

The reference catalog contains only **two exact UK Method variants**, with narrowly allowed glass/ceramic use cases. These are source-linked integration examples, not buying recommendations, safety certification, or a Finnish SKU database. A similarly named local bottle is not an exact match. Do not buy a product just to use the prototype.

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

`GQ_CHROMIUM_EXECUTABLE` can name an existing Chromium executable. Tests use a deterministic catalog-valid fixture date. The qualification suite exercises the generated HTML with an in-memory browser bridge plus a real-origin HTTP/PWA smoke. In this execution environment Chromium navigation to localhost is blocked by policy, so one service-worker/offline browser-origin test is skipped; the corresponding HTTP-origin shell, manifest, service worker and legal routes are still exercised directly. Physical-device HTTPS installation/camera behavior remains a separate release gate.

The latest current-source qualification records **245 Python/API/browser tests passed plus 34 client tests passed (279 passes total), with one environment-policy skip**, approximately 98% combined Python line/branch coverage, strict TypeScript 5.8.3 compilation and a byte-identical PWA rebuild. Railway separately proved a clean network install and startup of the refreshed runtime dependency lock. A disposable OSV audit then checked all 18 pinned Python runtime packages plus TypeScript 5.8.3 and reported **0 known vulnerabilities across 19 exact package/version queries**. A trustworthy OS-package scan of the final container/base image is still a release gate; an attempted disposable Trivy path did not yield inspectable evidence and is not counted as a pass.

## Architecture and handoff

- [Architecture and tradeoffs](docs/ARCHITECTURE.md)
- [Safety and catalog extension protocol](docs/SAFETY.md)
- [Privacy boundaries](PRIVACY.md)
- [Security model](SECURITY.md)
- [Test report](docs/TEST_REPORT.md)
- [Actual-cleaning demo script](docs/DEMO_SCRIPT.md)
- [Release checklist and validation plan](docs/RELEASE_GATES.md)
- [Build plan and completed iterations](docs/BUILD_PLAN.md)
- [Hackathon provenance](docs/HACKATHON_PROVENANCE.md)
- [Hosted deployment status](docs/HOSTED_STATUS.md)

CI is provided as a **manual-only GitHub Actions workflow**. The source is still hosted in the private GitHub repository `Smkz-Entertainment/GrimeQuest`; normal pushes do not trigger CI. Generated frontend bundles and qualification evidence are ignored by Git and can be regenerated locally; `scripts/package_release.py` includes generated runtime files and available evidence in a release archive.

The repo-backed Python service is deployed successfully on Railway. A temporary deterministic vision fixture and external qualification runner exercised the complete hosted HTTPS live protocol—authentication rejection, target observation, product transcription remaining unreviewed, eligibility/start, signed encounter, comparison, XP and idempotent repeat—then both temporary services were deleted and production was restored to AI-off-by-default. That qualification proves the network/application protocol, **not real model accuracy**. Physical phone/cleaning validation remains outstanding. The repository must still be made public before a hackathon submission that requires open source.

## License

Original application code and original illustrations: MIT. Dependency licenses remain their own. Product names and manufacturer material are third-party identifiers, not an endorsement; see [third-party notices](THIRD_PARTY_NOTICES.md).
