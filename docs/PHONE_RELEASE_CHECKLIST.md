# Physical phone and PWA acceptance checklist — release gate

**New always-available guided-play acceptance:** Start a real camera quest on an iPhone with no operator key; take two photos, confirm the safe user-known glass/tile target, choose the user-selected method, complete the five checks, make a real visible change, then self-report the outcome. Confirm no network image requests, guided-only XP, distinct SELF-REPORTED journal metadata, and no saved photos. Repeat without network after the app shell is cached. If AI Beta is enabled by the operator, verify it appears without any access code or server settings, still requires separate upload consent, and rejects unsupported tasks; if the model/limit/preflight is unavailable, local camera quests must remain usable.


**The Chromium integration suite does not replace this check.** Record device model, OS version, browser, installed-versus-tab mode, date, deployed Git commit and pass/fail for each item. Avoid recording personal images, addresses, product secrets or other sensitive content.

Test origin: [GrimeQuest HTTPS](https://grimequest-web-production.up.railway.app/). Production is intentionally **practice-only** until fixed-model qualification and privacy decisions are complete; do not bypass the server's private access controls.

## Installed app update/recovery (required before accepting photo-limit fix)
1. Install the previous build with its old cache-first worker, open the app and verify original local inventory survives page reload.
2. Publish the new build. Reopen the installed Home Screen app while online; the new worker must precache completely before activating. If an update arrives during a live task, no automatic reload may interrupt it.
3. If stale assets persist, open **Settings → Refresh or repair this installation**, tap **Refresh installed app**, and verify that the previous 12-MP warning no longer exists in the current app. Verify saved inventory and journal survive (do not record photos).
4. Verify /update.html, /update.js and /update.css respond with `Cache-Control: no-store` and are excluded from all service-worker cache allowlists, including the prior release's list; QR and offline shell remain functional.
5. Repeat from a real iPhone Home Screen app context; testing only a Safari tab is insufficient because installed web apps have separate storage. Test offline after recovery and ensure the worker is registered again.

## Offline practice and install (no AI required)

1. On a computer, open the HTTPS home page: confirm the QR code is visible and scans to the exact same-origin HTTPS root without third-party requests; verify the plain link and **Continue in desktop browser** work. Then open that HTTPS URL in iPhone Safari 17+ and a current Android Chrome browser if both are available. Confirm the page renders without horizontal scrolling at normal display scale.
2. Scan the desktop QR with the real phone camera and accept the URL banner. On iPhone tap **Share → Add to Home Screen** (enable **Open as Web App** when offered) / on Android Chrome use **Install app** when available. Open it from the icon; verify standalone display and app icon. Also test a browser without install-prompt support: the manual guidance must remain available.
3. Complete one **Practice** Grease Gremlin clear and one deliberately **unverifiable/partial** outcome. Confirm only clear yields practice XP, and that the journal labels the results **SIMULATED**.
4. Reload the page, switch tabs and reopen the installed app. Confirm inventory and practice journal persist, no duplicated clear XP appears, and interrupted live tasks cannot be silently forgotten.
5. While online, visit privacy and safety notices; then go offline and reopen the installed shell. Confirm practice/history remain available while live analysis explicitly reports that the network is required.
6. Turn on text enlargement, VoiceOver or TalkBack where available. Confirm focus labels, touch targets, error messages, choice groups and the ability to operate without visual animation.

## Local camera/file test (private testing only)

Camera analysis requires a separately authorized, private live configuration. The supported production URL must not have public AI enabled before the real safety evaluation. When an operator sets up a **private** test origin and access code:

1. Tap **Live camera**, grant camera access when prompted; confirm an actual rear-camera preview appears. Deny permission and ensure file-picker fallback and an explanatory message remain available.
2. Capture one ordinary, cool, unpowered, non-sensitive target. Confirm that the image is normalized locally to JPEG and that a separate explicit consent control appears **before** any upload.
3. Test file-picker alternatives: JPEG, PNG, WebP and an actual iPhone HEIC/HEIF photo. **Specifically test unmodified 24/48 MP phone photos larger than 8 MB for both product labels**, and a >12 MP target image. Verify they are accepted, resized locally to at most 1600 pixels per edge, remain correctly oriented and keep label text legible, with no upload before explicit consent. Safari 17+ can decode HEIC natively. On browsers without native HEIC decoding, confirm a specific **export JPEG** message appears. Unsupported SVG/RAW is rejected. Source files over 100 MB may still require an ordinary JPEG/HEIC export.
4. For the selected photo, test landscape/portrait rotation and background/resume. Confirm active camera tracks shut down on cancel, navigation, pagehide and document hidden. No camera stream should persist after leaving capture.
5. Reject upload consent and verify **no server/provider call** and no award occurs. Accept consent only after reviewing the configured image provider's privacy terms.
6. Test one deliberately uncertain material or unsupported cleaner. Confirm it cannot progress to a recommended chemical through a model guess or scanned bottle label alone.
7. For a real cleaning comparison, follow **exact current physical bottle and material instructions**, do not mix products, never use heat/electrical hazards, and separately assess visible **clear**, **partial**, **unchanged** and **unverifiable** cases. No disinfection claims.
8. Verify that duplicate after-photo requests do not award repeated live XP and that network outage/timeouts never substitute a practice-mode result as real AI.

## Evidence / sign-off

Record results in a private test sheet, not the public GitHub repository. Include only case IDs, device/browser details, app commit, timestamp, outcome and sanitized technical errors; do not attach unredacted photos.

**Go/no-go:** the release remains `NOT_READY_FOR_GENERAL_PUBLIC_LIVE_AI` if any real-model false clear or false supported recommendation, missing privacy consent, camera leakage, image-decoding crash, or absent provider/privacy owner detail remains. The owner keeps the repo private until explicit final publication approval.

## Real-world OCR qualification (must be performed on the phone)

1. On glossy and curved cleaning bottles, try close-up front and warnings photos with bright, even light, avoiding glare and background clutter. Repeat with Finnish and English print, 24/48 MP photos and portrait/rotated text.
2. Compare every recognized line to the actual bottle. **Garbled text such as `| MTT` or `LSANYTOL | VS` must never silently populate the product-name field.** If OCR is uncertain, the app must explain what happened and ask to retake or manually correct.
3. Saving an OCR transcription must require the user to confirm the text, including warnings, against the bottle. Without review, no product entry should be saved. Neither a successful OCR call nor that review may expand cleaning-product compatibility rules.
4. Verify both photos remain on the device until explicit OCR upload consent; server OCR does not send images to an external model or write picture/transcript files. When the service is busy or offline, manual entry stays available.
5. Measure word/name transcription accuracy and the rate of incorrect *apparently successful* scans on a small consented set of actual labels. Synthetic OCR smoke tests alone do not qualify real bottle accuracy.
