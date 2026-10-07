# Physical phone and PWA acceptance checklist — release gate

**The Chromium integration suite does not replace this check.** Record device model, OS version, browser, installed-versus-tab mode, date, deployed Git commit and pass/fail for each item. Avoid recording personal images, addresses, product secrets or other sensitive content.

Test origin: [GrimeQuest HTTPS](https://grimequest-web-production.up.railway.app/). Production is intentionally **practice-only** until fixed-model qualification and privacy decisions are complete; do not bypass the server's private access controls.

## Offline practice and install (no AI required)

1. Open the HTTPS URL in iPhone Safari 17+ and a current Android Chrome browser if both are available. Confirm the page renders without horizontal scrolling at normal display scale.
2. Use **Add to Home Screen** / **Install App**, open it from the icon, and verify standalone display and app icon.
3. Complete one **Practice** Grease Gremlin clear and one deliberately **unverifiable/partial** outcome. Confirm only clear yields practice XP, and that the journal labels the results **SIMULATED**.
4. Reload the page, switch tabs and reopen the installed app. Confirm inventory and practice journal persist, no duplicated clear XP appears, and interrupted live tasks cannot be silently forgotten.
5. While online, visit privacy and safety notices; then go offline and reopen the installed shell. Confirm practice/history remain available while live analysis explicitly reports that the network is required.
6. Turn on text enlargement, VoiceOver or TalkBack where available. Confirm focus labels, touch targets, error messages, choice groups and the ability to operate without visual animation.

## Local camera/file test (private testing only)

Camera analysis requires a separately authorized, private live configuration. The supported production URL must not have public AI enabled before the real safety evaluation. When an operator sets up a **private** test origin and access code:

1. Tap **Live camera**, grant camera access when prompted; confirm an actual rear-camera preview appears. Deny permission and ensure file-picker fallback and an explanatory message remain available.
2. Capture one ordinary, cool, unpowered, non-sensitive target. Confirm that the image is normalized locally to JPEG and that a separate explicit consent control appears **before** any upload.
3. Test file-picker alternatives: JPEG, PNG, WebP and an actual iPhone HEIC/HEIF photo. Safari 17+ can decode HEIC natively. On browsers without native HEIC decoding, confirm a specific **export JPEG** message appears. Unsupported SVG is rejected.
4. For the selected photo, test landscape/portrait rotation and background/resume. Confirm active camera tracks shut down on cancel, navigation, pagehide and document hidden. No camera stream should persist after leaving capture.
5. Reject upload consent and verify **no server/provider call** and no award occurs. Accept consent only after reviewing the configured image provider's privacy terms.
6. Test one deliberately uncertain material or unsupported cleaner. Confirm it cannot progress to a recommended chemical through a model guess or scanned bottle label alone.
7. For a real cleaning comparison, follow **exact current physical bottle and material instructions**, do not mix products, never use heat/electrical hazards, and separately assess visible **clear**, **partial**, **unchanged** and **unverifiable** cases. No disinfection claims.
8. Verify that duplicate after-photo requests do not award repeated live XP and that network outage/timeouts never substitute a practice-mode result as real AI.

## Evidence / sign-off

Record results in a private test sheet, not the public GitHub repository. Include only case IDs, device/browser details, app commit, timestamp, outcome and sanitized technical errors; do not attach unredacted photos.

**Go/no-go:** the release remains `NOT_READY_FOR_GENERAL_PUBLIC_LIVE_AI` if any real-model false clear or false supported recommendation, missing privacy consent, camera leakage, image-decoding crash, or absent provider/privacy owner detail remains. The owner keeps the repo private until explicit final publication approval.
