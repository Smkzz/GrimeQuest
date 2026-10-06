# GrimeQuest v0.1.0 — local qualification report

**Date:** 2026-10-06  
**Verdict:** Local prototype implementation and automated contract tests pass. **Real vision accuracy, physical cleaning, phone hardware and public deployment remain unqualified.**

## Executed results

| Check | Observed result |
| --- | --- |
| Python/API/policy/image/provider tests | 221 passed |
| Chromium UI integration tests | 14 passed; included in the 235-test Python run |
| TypeScript-domain / storage / camera-lifecycle / service-worker Node tests | 34 passed |
| Total automated test cases | **269 passed, zero failed, zero skipped** |
| Client/server compatibility parity | 840 combinations agree; this is one property test, not 840 extra test cases |
| Strict TypeScript 5.8.3 compilation | Pass |
| Python combined line/branch coverage | **97.68%** |
| Python statement coverage | 494 / 504 lines (98.02%) |
| Python branch coverage | 137 / 142 branches (96.48%) |
| Policy, strict schemas, provider adapter and receipt modules | 100% measured coverage in this suite |
| Rebuild of generated client/catalog/assets/preview | Byte-identical |
| Fresh-process HTTP smoke | Server starts; actual served JS matches build; security headers present; unconfigured live POST returns 503 |
| Paid / real provider calls | **0** |
| External repository/CI/deployment actions | **0** |

## What the browser tests establish

The actual compiled application was exercised in Chromium 144.0.7559.96 at 1440, 768, 390 and 320 pixel widths. Home and complete practice flows had no horizontal overflow in these tests. The suite covers positive completion, partial retry, missing care checks, unsupported material, unreviewed labels, inventory removal, escaped malicious text, corrupted-store recovery, interrupted-task warnings, exported journal payloads, keyboard focus, image descriptions and a complete browser-to-FastAPI flow with an injected vision component.

The environment blocks browser URL navigation and hardware camera capture by policy. The browser suite uses `set_content` with the generated HTML, explicitly in-memory Storage objects, and a fetch bridge to FastAPI TestClient. It does **not** establish real browser origin behavior, persistent storage, service-worker installation, offline reload, HTTPS deployment, physical cameras, iOS Safari or Android-device correctness. HTTP/ASGI security and service-worker routing were tested separately. No browser policy was disabled.

## Adversarial cases and corrections

Tests exercise extra/injected model fields, malformed JSON, refusals, truncation, provider failures and timeouts; no-result paths do not mint success or XP. Images are tested for malformed base64, type mismatch, excessive pixels, animation, transparency and metadata stripping. Receipts are tested for forgery, purpose confusion, expiry, changed catalogs, swapped before images, identical before/after bytes, repeated completion and concurrent verification.

During iteration, numeric consent (`1` or `1.0`) was found to pass a literal-boolean schema and was explicitly rejected. Missing client attestations no longer pass by an empty-object check. Non-ASCII access headers fail without a type error. Image decoding now has its own two-slot bound. UI iteration guarded stale file decodes and interrupted live mode switching, preserved corrupted local data, exposed unsupported product state and improved phone input/touch-target sizing.

## Reproducibility and scope

Tests ran on Python 3.13.5, Node 22.16.0, TypeScript 5.8.3 and Chromium 144.0.7559.96 with installed dependency versions recorded in the lock files. Catalog tests use a fixed valid fixture date; actual application catalog expiry is unchanged. Model observations and cleaning pictures in tests are synthetic. The 28-second interface walkthrough is labeled practice throughout, not a real-task demo.

Coverage measures exercised code, not security, chemical safety, model accuracy or product-market fit. Current dependency-advisory scanning, a clean network install, a built/scanned container, hosted CI, an independent security review, actual manufacturer/chemical expert validation and real-device cleaning trials were not completed. The two source-linked UK product entries are deliberately narrow integration examples, not a broadly usable local-product catalog.

## Evidence files

The internal qualification run generated `pytest.log` / `pytest.xml`, a separate browser repeat, Node-test logs, coverage data, build checks, HTTP smoke results, responsive screenshots and a labeled UI walkthrough under `evidence/`. Those generated artifacts are intentionally ignored by Git in the source repository. They can be regenerated locally and are included by `scripts/package_release.py` when present. The release packager writes `BUILD_MANIFEST.json`, hashes every included source/evidence file, and reads the ZIP back against those hashes.

See `docs/RELEASE_GATES.md` for the remaining physical/live/public qualification work. No real cleaning outcome is claimed by this report.
