# Changelog

All notable changes to the **public monster-game release** are recorded first.
Older entries are preserved as historical development notes; they document
prototype barcode/AI/cleaning-policy experiments that are **not** visible in
the current self-reported player experience.

## [0.1.0] — 2026-10-09 — Public monster-game release candidate

### Added

- A no-account, camera-first **Find → Clean → Defeat** game where a safe real
  cleaning chore defeats a fictional grime creature and awards 300
  **self-reported** XP after before/after photos.
- Six original collectible SVG monsters (Smudgie, Dusty, Crumb Goblin,
  Splodge, Grubble and Lord Grime), local collection, level progression,
  and a reduced-motion-aware defeat celebration.
- An explicitly illustrated **zero-XP demo** that cannot modify the journal,
  collection, or saved player progress.
- A keyboard-operable before/after photo comparison slider, optional visual
  alignment guide, text-only sharing and resumable in-session quests.
- Dedicated public-release documentation, responsible disclosure guidance,
  accessibility/support documents, a safer Git-index-only release packager
  and release-archive integrity tests.

### Preserved and protected

- Local-only photos for the public game; no account, runtime AI requests,
  compulsory product/cleaner selection, cloud photo library or analytics.
- Fixed, idempotent, provenance-marked XP; duplicate scoring and identical
  before/after image content are rejected. Old progress remains compatible.
- Existing guarded legacy server/product endpoints remain outside the
  shipped casual UI; they are not chemical-safety advice.
- The public game's independent Railway clean-room baseline:
  **534 Python/API/Chromium/PWA + 61 Node = 595 passed** on the
  monster candidate, Python combined coverage 90.43%.
  These are software tests, not physical iPhone/hygiene certification.

### Known limitations

- An actual iPhone Home Screen/HEIC and live household cleaning trial must
  be accepted independently; not every hardware/browser variant was tested.
- The game cannot verify cleaning, identity, hygiene or chemical suitability.
- XP and creature collection are local to the device and can be edited/lost.
- The repository has no published GitHub Release/tag at the time this
  candidate documentation was written. Publishing one is a separate
  maintainer action described in [RELEASING](docs/RELEASING.md).

---


## 2026-10-08 — Surface-wide guided quests

- Unblocked the **self-reported camera-quest flow** for steel, natural stone, wood, cool unpowered glass-ceramic hobs, limescale and any other known material the player names.
- Preserved required material/care checks and unknown/hazard stops; no scanned, manually entered or catalog product automatically gains additional chemical-use permission.
- Allowed players to choose an existing Arsenal item as their **own unverified method** in guided mode; improved material and soil labels and safety wording.
- Expanded Node state-machine and browser regression tests, without changing the model-reviewed catalog's conservative eligibility decisions.


## Native iPhone HEIC photo support — 2026-10-08

- Added iOS Safari 17+ native HEIC/HEIF photo selection and browser JPEG normalization; no WASM dependency or image-upload bypass.
- Improved unsupported-browser fallback and preserved 8 MB file limit / SVG exclusion.
- Added upload-format regression tests for both live target and product-label pickers.
- Clean-room release candidate: **449 automated tests passed** (413 Python/browser + 36 Node), 97.76% Python coverage, reproducible generated PWA; physical-device testing remains open.
- Refreshed all five official manufacturer links and added a device/cleaning acceptance checklist.

## Fixed Gemini 2.5 Flash Lite ZDR smoke — 2026-10-08

- Under a narrow owner authorization, issued exactly three live, low-cost fixed-model image-analysis calls using a Railway-isolated test runner; all HTTP 200, model identity stable, structured output valid and ZDR routing required.
- Two public reference-photo target observations abstained from unsupported product recommendations; different physical before/after images were marked non-comparable.
- Immediate OpenRouter account-usage delta read 0; actual settled billing may differ. The trial does not qualify model accuracy or public privacy consent.
- Production live AI remains off, the existing $0.50 dedicated-key requirement for full labeled evaluation remains in the actual runner, and all temporary qualification services were removed.

## ZDR evaluation safeguards — 2026-10-08

- Require zero-data-retention routing and deny model-provider data collection.
- Require a non-resetting, provider-verified key budget and eligible fixed-model ZDR endpoint before evaluation.
- Clean-room result: 446 tests passing, 97.76% Python coverage, reproducible build.
- No inference billed in this qualification wave.

## Runtime image hardening — 2026-10-08

- Removed unused pip/build-time Python packages after installing, checking and import-testing the runtime dependencies; production Dockerfile canary passed.
- Trivy 0.74.0 whole-rootfs HIGH/CRITICAL scan of the equivalent remediated runtime passed. The Trivy executable is not shipped and was excluded from its own audit.
- Verified OpenRouter key, but declined to enable live AI: Qwen free unavailable, one successful free-router observation, another routing 404, fixed Gemma ZDR-required 404. No paid inference.
- Repository remains private; public practice mode stays available and safe-fail-closed.

## Exact-pair vision-evaluation hardening — 2026-10-07

- Removed the false-supported evaluation case where a known surface and known soil were incorrectly combined despite no reviewed product covering that exact pair.
- Linked evaluation candidate pairs to enabled reviewed catalog rules and added 36 regression cases (35 matrix combinations plus one explicit counterexample).
- Clean-room evidence: **405 Python + 34 client tests = 439/439 passing**, 97.55% Python coverage and byte-identical build; no real vision model or physical cleaning claims.

## Release hardening wave — 2026-10-07

- Added persistent workflow signing across restarts.
- Added stricter cross-origin/browser headers and suppressed the server fingerprint.
- Added standalone privacy/safety pages to the PWA offline shell.
- Improved contrast, reduced-motion and forced-colors accessibility behavior.
- Refreshed runtime dependencies; pinned Docker bases by digest; added `pip check`; aligned project metadata.
- Added real-origin PWA qualification tests.
- Upgraded vision transport to strict JSON-schema structured output and OpenRouter parameter-support enforcement.
- Qualified the complete public-HTTPS live protocol with temporary deterministic mock infrastructure, then deleted the infrastructure and restored AI-off-by-default.
- Added 0.5 vCPU / 0.5 GB Railway resource ceilings.
- Final clean-room automated result: **439/439 passes**, zero skips/warnings; 97.55% Python coverage; 1,680 client/server policy combinations agree.
- Added three exact Finland-market Kiilto consumer spray variants (Ikkuna, Koti, Keittiö; fragrance-free 600 ml) without broadening the supported surface classes.
- Added a 320/390 px expanded-loadout regression; fixed a real 320 px overflow from long Finnish product names.
- Kept Railway edge tracing while explicitly disabling FastAPI-native telemetry/OTLP auto-configuration to remove startup errors and avoid duplicate application telemetry.
- Added a privacy-preserving real-model qualification harness with safety-critical false-supported, hazard-miss and false-clear gates.
- Added a Python 3.13 clean-room Railway qualification image and removed the obsolete public OpenAPI schema.
- Fixed live quest resumption so an equipped product removed from the real arsenal cannot remain a stale loadout.
- Added an opt-in, rate-limited public demo access mode so judges can use live analysis without a distributed shared secret; default remains private/off.
- Added global daily provider-attempt ceiling and deployed commit provenance in health.
- Enabled Railway edge tracing without Python auto-instrumentation; capped production at 0.5 vCPU / 0.5 GB.
- Full OSV audit: 32 exact runtime/test/TypeScript package-version queries, 0 known vulnerabilities after catching and fixing pytest 9.0.2; final OS-package/container scan remains unqualified.

## Deployment hardening — 2026-10-06

Repo-backed Railway deployment qualified on exact source commit `a7acac65c79db80e5e86516d2b196bd25503c21b`. Added deployment-time PWA compilation, Railway `PORT` support, Amsterdam deployment configuration, platform health checking, and a narrow health-probe Host exception. The full local regression suite remained green (269 tests). The temporary practice-only Railway Function was removed after the production service became healthy. Live AI and physical cleaning validation remain outstanding.

## Unreleased

- Build generated PWA assets inside the deployment image instead of assuming checked-in bundles.
- Honor the platform-provided `PORT` at runtime.
- Configure Railway healthcheck, bounded restart policy and Amsterdam region at the service level; deprecated repository JSON config was removed.
- Publish an explicitly practice-only HTTPS walkthrough on Railway while the private-repository GitHub authorization remains blocked.

## 0.1.0 — 2026-10-06

Initial local prototype: mobile-first quest PWA, original practice scenarios, real-inventory workflow, bounded vision adapter, source-linked conditional product policy, explicit consent, signed workflow receipts, visual-comparison game states, local journal, interrupted-task recovery, source tests and release documentation.

Known qualification gaps: real vision accuracy, physical phone/camera trials, actual cleaning outcomes, expert-reviewed broader local catalog, hosted CI, clean network install, current dependency advisory scanning and production operational controls. Practice results are intentionally simulated.
