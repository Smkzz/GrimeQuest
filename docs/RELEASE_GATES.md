# Release gates

## Zero-setup camera quests — functional fallback

The default guided camera mode can run entirely on the phone, even if the remote vision provider is unavailable: before photo, user-known surface/soil, explicitly user-selected method, care confirmations, after photo and **self-reported** visible outcome. It awards separate guided XP, **not** model-observed XP, and never treats a self-report as chemical advice or a certified hygiene measurement. Photos are never uploaded in guided mode. Unknown materials/soils, unverified custom materials, hazards and identical before/after photos cannot earn a guided clear. Any known user-confirmed material and visible soil—including stone, wood, steel, cool unpowered hobs, mineral deposits and explicitly named other materials—can use the independent self-selected-method flow; this does not enlarge the reviewed chemical-product catalog. Physical iPhone acceptance remains outstanding.

## Software release candidate — qualified

The current software architecture and automated implementation are ready for the remaining empirical gates.

Clean-room evidence:

- **413 Python/API/browser/evaluation tests passed**
- **36 client tests passed**
- **449 / 449 total in the historical October 7 baseline; newer commits require a new full-suite run**
- **97.76% combined Python coverage**
- **1,680 client/server policy combinations agree**
- Python 3.13.16 / Node 22.23.3 / TypeScript 5.8.3
- real-origin PWA/service-worker/offline-shell test passes in Chromium
- byte-identical generated rebuild
- npm clean install: zero vulnerabilities
- OSV: 32 exact package/version queries, zero known vulnerabilities
- hosted HTTPS application protocol passed with deterministic observations

Practice and mock-provider evidence remain explicitly separated from real AI/physical-cleaning evidence. The candidate-space evaluator now derives exact surface–soil combinations from the reviewed catalog instead of using a cross-product of independently supported fields.

A subsequent **exploratory Gemini 2.5 Flash Lite** fixed-model test produced three valid live ZDR-required observations (including a correctly unverifiable comparison). This is not an independent 54+ case accuracy validation; see [evidence](REAL_FIXED_ZDR_TRIAL_20261008.md). Production live AI remains off.

Native HEIC/HEIF upload acceptance and browser error fallback are now source/test qualified for Safari 17+, but still require the actual-device [phone acceptance checklist](PHONE_RELEASE_CHECKLIST.md) before a real-image launch.

## Limited owner-authorized AI beta configuration

Optional public preview traffic is strictly operator-configured; players never supply an API key or touch server settings. The server chooses only `google/gemini-2.5-flash-lite` on OpenRouter for this bounded beta, and performs **read-only** metadata verification of an existing non-resetting total key cap (at most $10) and supported ZDR/structured-output endpoint before any image inference. Every actual request independently requires ZDR and denies provider data collection. The operator must use narrow `GQ_MAX_CALLS_HOUR` and `GQ_MAX_CALLS_DAY` values (the in-memory request counter resets on restart, so it is not a dollar budget), and the shared provider-side cap remains the last-resort spending ceiling. If any check fails, the AI feature fails closed and guided quests remain playable. This beta is **not** certified for generalized cleaning advice; full independent labeled evaluation and physical tests remain mandatory before a general public real-world launch.

## Cloud Vision product-label OCR readiness

- The Tesseract local OCR path is retired. Automatic product label reading remains operator-disabled unless the GrimeQuest-hosted Google Cloud Vision EU API key, project and explicit activation flag are configured.
- Confirm Google Cloud Vision API enabled on its own billing-controlled project; restrict the API key to Cloud Vision only; configure quota/billing controls and privacy/controller contact. A billing alert alone is **not** a hard spending cap.
- Verify front/back label OCR with actual consented Finnish and English bottle photos, measure name/directions/warnings accuracy and errors, and require explicit human review. No OCR text unlocks cleaner recommendations.
- Verify the bundled mock-transport Cloud Vision REST contract and the public server's same-origin, consent and request-size controls before activation.
- Google Vision OCR is separate from unqualified general-purpose AI cleaning analysis, which remains fail-closed.

## Before the first real-model / physical demo

1. Confirm the organizer's exact build-week eligibility/rules for AI-generated code/assets. Do not backdate work.
2. Choose the exact real vision model/endpoint. Accept its image privacy/retention terms and document availability/quota/cost behavior.
   - Before *any paid qualification request*, verify a separate OpenRouter key with a hard non-resetting ≤US$0.50 total cap (including BYOK) and ZDR-only routing. The existing shared key does not qualify.
3. Run `scripts/evaluate_provider.py` against the private labeled image set and satisfy every safety-weighted gate in `eval/README.md`.
4. Use an exact reviewed product variant actually owned by the tester and an independently known supported surface. Read the real bottle and surface-care instructions.
5. Test the deployed HTTPS PWA on the actual phone: permission grant/deny, camera capture, rotate, background/resume, track shutdown, file fallback, persistent storage, installation and offline shell.
6. Run controlled physical cases for clear, partial, unchanged/unverifiable outcomes. Keep abstentions/failures visible.

## Before a general public live-image launch

- Equivalent runtime Trivy rootfs HIGH/CRITICAL audit passed after removing unused Python tooling, and the actual Dockerfile passed a canary healthcheck. Before general public launch, obtain independent security review and, where possible, an exact final published-image scan; do not conflate the original vulnerable base with the remediated runtime.
- Independently review security and the narrow product/material rules at a level appropriate to the audience.
- Perform actual screen-reader and target-device accessibility review.
- Add the final service/operator privacy identity/contact and provider-specific processing/retention information.
- For broad multi-user use, replace process-local quotas/result caches with durable controls appropriate to the expected traffic. The hackathon public-demo mode is intentionally bounded and is not an internet-scale account system.
- Monitor provider cost/quota and abuse behavior under the intended launch load.
- Continue catalog expansion only from exact manufacturer evidence; OCR/model output can never create permissions.

## Submission switch

The repository intentionally remains private during final preparation. Make it public only when ready to submit, then verify:

- license / README / privacy / safety render publicly;
- no credentials or private evaluation images exist in history;
- the demo URL is healthy;
- the deployed source is the qualified release ref;
- live AI is enabled only if the real-model and physical-device gates above have passed.

## Product validation after the hackathon

Test the underlying utility without relying on XP: **“Which of my products can I use on this target?”** Measure setup friction, supported-product coverage, model abstention, false-supported rate, false-clear rate and actual chore completion. Do not invest first in leaderboards, marketplaces or broad chemical coverage.
