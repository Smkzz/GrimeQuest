# Changelog

## Deployment hardening — 2026-10-06

Repo-backed Railway deployment qualified on exact source commit `a7acac65c79db80e5e86516d2b196bd25503c21b`. Added deployment-time PWA compilation, Railway `PORT` support, Amsterdam deployment configuration, platform health checking, and a narrow health-probe Host exception. The full local regression suite remained green (269 tests). The temporary practice-only Railway Function was removed after the production service became healthy. Live AI and physical cleaning validation remain outstanding.

## Unreleased

- Build generated PWA assets inside the deployment image instead of assuming checked-in bundles.
- Honor the platform-provided `PORT` at runtime.
- Add `railway.json` with healthcheck, bounded restart policy and Amsterdam deployment region.
- Publish an explicitly practice-only HTTPS walkthrough on Railway while the private-repository GitHub authorization remains blocked.

## 0.1.0 — 2026-10-06

Initial local prototype: mobile-first quest PWA, original practice scenarios, real-inventory workflow, bounded vision adapter, source-linked conditional product policy, explicit consent, signed workflow receipts, visual-comparison game states, local journal, interrupted-task recovery, source tests and release documentation.

Known qualification gaps: real vision accuracy, physical phone/camera trials, actual cleaning outcomes, expert-reviewed broader local catalog, hosted CI, clean network install, current dependency advisory scanning and production operational controls. Practice results are intentionally simulated.
