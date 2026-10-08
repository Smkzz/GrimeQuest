# Final launch-critical review — 2026-10-08

**Release candidate qualified:** `4beda16d6c212cd5e15091daa81cae6135ba1589`, tested on an isolated Railway qualification service using `Dockerfile.qualify`. Changes made after this source identity are documentation-only. **Primary product:** private, self-reported guided camera quests with optional practice tutorial. AI preview is experimental and operator-governed, not a prerequisite for gameplay.

## Objective validation

| Gate | Evidence |
| --- | --- |
| Strict TypeScript 5.8.3 and generated PWA | PASS, byte-identical rebuild |
| Node/client state, offline, scanner and camera tests | **60/60 PASS** |
| Python/API/policy/browser/real-origin PWA tests | **509/509 PASS** |
| Total collected automated tests | **569/569 PASS** |
| Python combined statement/branch coverage | **90.43%** (minimum 90%) |
| Python warnings | 252 non-failing warnings, predominantly FastAPI `on_event` deprecations and test tooling; **not** a zero-warning claim |
| Paid AI requests in this qualification | 0 |
| External GitHub Actions CI cost | 0 |
| Device acceptance | Chromium desktop/mobile emulation and real localhost origin covered. **Physical iPhone/Safari still unverified.** |

The pre-audit production source `b878036` failed **13 of 506** broad Python/browser/PWA tests; the first correction reduced this to **one of 509**. Root causes: outdated test assumptions from retired front/back OCR and renamed messages, the clean-room image missing the exact ZXing scanner asset bundled by production, a brittle cross-category field-order test and ambiguous UI test selectors. All have been corrected, and the no-network scanner and product flows were retested. The final live version must also pass its separate production Docker smoke and Railway `/api/health` gates; this document does not by itself attest the public deployment.

## Player-journey inspection and implemented improvements

| Stage | What a new player can now do | Regressions guarded |
| --- | --- | --- |
| Arrive | Open playable app immediately on desktop or phone; installation QR/instructions are **opt-in**, not a blocking screen or pop-up | Real-origin desktop/iPhone/Android install tests |
| Start | **Start camera quest** with no signup, API key or paid service; remain in guided mode even if optional AI becomes available | Public-AI opt-in test |
| Capture | Open camera then enable Take photo only when the video is ready, or select a JPEG/PNG/WebP/native-supported HEIC/HEIF photo locally | Browser photo, resize and privacy tests |
| Identify | Choose known steel, wood, stone, glass, ceramic, cool unpowered hob or name another known material; choose visible grime/mineral deposits | Guided surface/soil state matrix plus browser cases |
| Safely choose method | Choose own independently checked method or owned Arsenal product; **no unreviewed cleaner receives chemical-use permission**; unknown materials/hazards still blocked | Node/client/backend policy isolation and cross-mode tests |
| Continue | Selecting a guided method now **opens care checks immediately**; no hidden extra Continue button below fold | Guided end-to-end browser tests |
| Clean | Complete five explicit target/product/tool/surface precautions; app never supplies dangerous concentrations, mixtures or unverified procedures | Policy/attestation tests |
| Finish | Take comparable dry after photo; explicitly self-report clear/partial/unverifiable; identical photos cannot claim a clear | Browser outcome tests, separate provenance and no duplicate XP |
| Review | Receive guided-only XP, open journal, and retain local inventory and completion history without saving photo bytes | Persistence, export, PWA offline tests |
| Recover | Installed-app refresh/recovery never silently erases saved inventory; interrupted chemical-use warning is preserved | Service-worker and recovery tests |

## Honest UX verdict

**Stronger and launch-candidate-quality for the default guided loop, but an externally verified `10/10` is not established.** Automated Chromium coverage is valuable but cannot replace a real iPhone Home Screen app test, hands-on observation of first-time player comprehension or independent accessibility review. More features are not the priority for this deadline; accepting the current reliable no-key loop is more valuable than adding unqualified AI or untested mechanics.

### External blockers before publishing or claiming universal quality

1. **Physical device acceptance:** iPhone Safari and installed PWA, native camera/HEIC, background recovery, 320/390px UI, touch targets and VoiceOver; perform complete before/after quest, XP and journal on the real device.
2. **International product coverage:** Test the physical Sanytol barcode and additional products across countries. No barcode database is exhaustive. Google-backed Serper fallback is disabled without an operator-only key and a verified provider-side spend cap. Keep the manual name route.
3. **Public source and submission:** Repository remains private until owner publishes it after a secret/PII review. Confirm public GitHub URL, working hosted URL, required real-task demonstration video and actual submitted state before the deadline.
4. **AI preview and privacy:** Production AI preview has a spend-cap preflight blocker; do not imply AI-verified real-world outcomes. The public privacy policy still needs final operator/contact/legal details before general-purpose live AI processing.
5. **Deprecations and independent validation:** FastAPI lifecycle deprecation warnings and independent physical cleaning/materials evaluation remain technical debt. They do not expand permissions from the reviewed catalog.

## Ship decision

**GO for a judge-tested, private-photo, self-reported guided cleaning game once the exact live deployment is healthy and the physical-phone smoke succeeds. NO-GO for claiming globally reliable barcode recognition, general chemical compatibility, AI-verified cleaning or objective 10/10 mobile usability.** The five reviewed product variants remain narrow demo references, distinct from worldwide barcode identity suggestions. 
