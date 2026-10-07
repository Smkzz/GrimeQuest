# GrimeQuest v0.1.0 — current-source qualification report

**Date:** 2026-10-07  
**Verdict:** Current source, deterministic policy, PWA build and hosted application protocol qualify. **Real vision accuracy, physical cleaning and target-phone camera/install behavior remain unqualified.**

## Executed results

| Check | Observed result |
| --- | --- |
| Python/API/policy/image/provider/browser tests | **245 passed, 1 skipped** |
| TypeScript-domain / storage / camera-lifecycle / service-worker Node tests | **34 passed** |
| Total passing automated test cases | **279 passed** |
| Environment-policy skips | **1** — Chromium navigation to localhost is blocked in this runtime |
| Strict TypeScript 5.8.3 compilation | Pass |
| Python combined line/branch coverage | approximately **98%** |
| Provider adapter coverage | **100%** in this suite |
| Rebuild of generated client/catalog/assets/preview | Byte-identical |
| Real-origin HTTP PWA smoke | Pass |
| Railway clean dependency install / Docker build / healthcheck | Pass |
| OSV advisory audit of exact Python runtime pins + TypeScript | **19 checked, 0 vulnerable, 0 errors** |
| Final OS-package/container image scan | **Not qualified** — attempted Trivy path did not yield inspectable scan evidence |
| Hosted public-HTTPS protocol qualification | **PASS with deterministic mock vision provider** |
| Paid / real provider calls | **0** |
| GitHub Actions consumed | **0** |

## Current-source browser/PWA qualification

The current generated application is covered at desktop and phone widths by the browser integration suite. A new real-origin PWA test starts the actual server and is designed to verify service-worker registration, app-shell caching, offline reload and standalone legal routes. The execution environment blocks Chromium navigation to localhost, so that browser-origin test is skipped rather than bypassing the policy. A sibling real HTTP-origin test still verifies that `/`, `app.js`, `styles.css`, `manifest.webmanifest`, `sw.js`, `privacy.html`, `safety.html` and `robots.txt` are served, and that security headers and service-worker allowlisting are correct.

This does not establish iOS Safari, Android Chrome, physical camera, Add to Home Screen or offline behavior on the target phone. Those are explicit manual release gates.

## Hosted end-to-end protocol qualification

A temporary Railway vision fixture returned deterministic schema-valid observations and a separate temporary Railway runner acted as an external client through the public production HTTPS origin. The run established:

- health returned 200 with live mode configured and persistent workflow signing enabled;
- a wrong access code returned 401;
- target analysis returned a schema-valid glazed-ceramic / grease observation and signed target ticket;
- product-label analysis returned `review_status=unreviewed` and `recommendation_permission=false`;
- policy/start returned an eligible match and signed encounter ticket;
- before/after verification returned clear, fixed 300 XP and a signed completion receipt;
- repeating the same verification returned the same receipt (idempotent);
- root, manifest, service worker, privacy, safety and robots routes all returned 200.

Qualification log marker: `GQ_QUALIFICATION_PASS` on temporary deployment `52e34e89-4386-461e-9902-979dfa4a0b3e`.

Both temporary services were deleted immediately afterward and production was restored to AI-off-by-default. **This proves the hosted protocol and trust boundaries, not the visual accuracy of any real model.**

## Public-demo access qualification

A separate opt-in access mode allows a judging/public demo to use live analysis without distributing a shared secret. It is disabled by default. Server configuration rejects public mode unless persistent workflow signing is configured and the daily attempt ceiling is at most 200. Automated tests establish that private mode still requires the access code, public mode succeeds without it, and cross-origin requests remain rejected. The browser integration test confirms the public-mode UI hides the access-code field and can reach the live target-analysis flow.

## Security/reproducibility changes since the first report

- persistent HMAC workflow signing secret;
- strict JSON-schema provider response format plus independent Pydantic validation;
- OpenRouter routing can require endpoints that support every requested parameter;
- additional COOP/origin-agent/cross-domain headers;
- suppressed Uvicorn Server header;
- privacy and safety pages included in the offline shell;
- improved text contrast, reduced-motion and forced-colors support;
- Docker bases pinned by digest;
- refreshed exact runtime dependency lock and synchronized project metadata;
- Docker build fails on `pip check` conflicts;
- Railway per-replica resource ceiling: 0.5 vCPU / 0.5 GB.

## Known remaining evidence gaps

1. No real vision-provider request or model-accuracy qualification has been run.
2. No physical phone camera/install/offline test has been run.
3. No real cleaning sequence has been run against the live model.
4. No independent chemical/material expert review has broadened the tiny product catalog.
5. Exact application-package advisory queries are clean in OSV (19/19 exact package versions). A trustworthy OS-package/final-container image scan and independent security review remain outstanding.
6. Repository visibility remains private until the owner deliberately opens it for submission.

No practice fixture or mock-provider output should be described as real AI or physical-cleaning evidence.
