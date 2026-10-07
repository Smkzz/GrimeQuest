# Changelog

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
- Final clean-room automated result: **403/403 passes**, zero skips/warnings; 97.55% Python coverage; 1,680 client/server policy combinations agree.
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
