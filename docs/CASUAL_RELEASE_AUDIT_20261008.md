# GrimeQuest casual launch acceptance — October 8, 2026

## Verdict
**Software qualification passed for the streamlined self-reported game loop.** The full player-facing experience is: **Snap the dirt → Clean it → Snap again → Claim +300 XP**. No account, material/soil classification, cleaner/product selection, barcode, AI setting or purchase is in the visible casual experience. Camera activation is gesture-controlled and photos remain on device.

### Audited functional source
- Source branch: launch/casual-clean-loop-20261008
- Qualified functional commit: f2e8e75afe4681c0afac1d8d849cc556a26a7a28
- Build: isolated Railway Dockerfile.qualify, Node 22, Python 3.13.16, Chromium, clean pinned dependencies
- Exact source emitted GQ_CLEAN_ROOM_QUALIFIED on October 8, 2026
- 61/61 Node domain/storage/camera/PWA tests passed
- 520/520 Python/backend/Playwright/real-origin PWA tests passed
- Total **581/581 automated tests PASS**
- Combined Python line+branch coverage: **90.43%**, meeting 90% threshold
- PWA rebuild byte-identical; strict TypeScript 5.8.3 passed
- Provider inference requests: 0; GitHub Actions triggered: 0
- 252 non-failing warnings, mainly deprecated FastAPI on_event integration. **Not zero warnings.**

### Player perspective & changes
1. **Start quickly:** playable directly on mobile and desktop; optional QR and installation controls do not interrupt first use.
2. **First photo:** tap the large start button; camera permission requested only after player action; capture disabled until stream ready; local file-photo fallback.
3. **No menus:** neither surfaces nor cleaning products are classified or selected. The app never recommends a chemical or changes its label/care instructions.
4. **Clean:** a simple before-photo reference, an obvious next action, no countdown, no rewards for excessive cleaning.
5. **After photo:** repeat the same frame if possible; exactly one "not yet" action, and one explicit "It’s clean! +300 XP" confirmation.
6. **Rewards:** before+after photos must differ, scoring is self_attested and idempotent, previous guided history is preserved, no live-AI XP claims.
7. **Recovery:** My wins and Settings can be visited during a quest without discarding in-memory progress. Browser reload still loses unfinished images by design; no photo data is saved in localStorage.
8. **Offline:** after PWA cache install the casual loop runs without backend API calls; static app shell and photos remain local.
9. **Privacy:** settings reset requires confirmation and clears legacy session access code and local data. No analytics or user account.

### Release blockers outside automated QA
- **Actual iPhone hardware**: Rear camera permission grant/deny, native HEIC photo input, Safari Home Screen PWA, background lifecycle, accessibility and a complete first-person before/after/XP/journal demonstration have not been independently observed in this run. Use CASUAL_PHONE_ACCEPTANCE_20261008.md.
- **Real-world cleaning**: Software cannot prove the user cleaned the surface, that an object is hygienic, or that a selected product is suitable; outcomes are explicitly self-reported. Don't claim AI recognition.
- **Hackathon submission**: Repo is PRIVATE until the owner reviews and publishes source; a real-task video and final submission confirmation are separate owner steps.

### Decision
**GO for technical deployment of a casual, self-reported cleaning game once the exact merged production Docker build and Railway healthcheck pass.** No claim of objective 10/10 physical iPhone UX without hands-on acceptance, no generalized material/chemical advice and no AI verification claim. Do not add new major features within the launch window.
