# Release gates

## Software release candidate — qualified

The current software architecture and automated implementation are ready for the remaining empirical gates.

Clean-room evidence:

- **369 Python/API/browser/evaluation tests passed**
- **34 client tests passed**
- **403 / 403 total; zero skips/warnings**
- **97.55% combined Python coverage**
- **1,680 client/server policy combinations agree**
- Python 3.13.16 / Node 22.23.3 / TypeScript 5.8.3
- real-origin PWA/service-worker/offline-shell test passes in Chromium
- byte-identical generated rebuild
- npm clean install: zero vulnerabilities
- OSV: 32 exact package/version queries, zero known vulnerabilities
- hosted HTTPS application protocol passed with deterministic observations

Practice and mock-provider evidence remain explicitly separated from real AI/physical-cleaning evidence.

## Before the first real-model / physical demo

1. Confirm the organizer's exact build-week eligibility/rules for AI-generated code/assets. Do not backdate work.
2. Choose the exact real vision model/endpoint. Accept its image privacy/retention terms and document availability/quota/cost behavior.
3. Run `scripts/evaluate_provider.py` against the private labeled image set and satisfy every safety-weighted gate in `eval/README.md`.
4. Use an exact reviewed product variant actually owned by the tester and an independently known supported surface. Read the real bottle and surface-care instructions.
5. Test the deployed HTTPS PWA on the actual phone: permission grant/deny, camera capture, rotate, background/resume, track shutdown, file fallback, persistent storage, installation and offline shell.
6. Run controlled physical cases for clear, partial, unchanged/unverifiable outcomes. Keep abstentions/failures visible.

## Before a general public live-image launch

- Complete an inspectable OS-package/final-container vulnerability scan. Application-package OSV checks are clean, but that is not an OS image scan.
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
