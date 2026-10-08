# Physical phone and PWA acceptance checklist — release gate

**New always-available guided-play acceptance:** Start a real camera quest on an iPhone with no operator key; take two photos, confirm a user-known safe target such as glass, tile, steel, stone, wood or a cool unpowered hob, choose the user-selected method, complete the five checks, make a real visible change, then self-report the outcome. Confirm no network image requests, guided-only XP, distinct SELF-REPORTED journal metadata, and no saved photos. Repeat without network after the app shell is cached. If AI Beta is enabled by the operator, verify it appears without any access code or server settings, still requires separate upload consent, and rejects unsupported tasks; if the model/limit/preflight is unavailable, local camera quests must remain usable.


Also test **Other known material** by entering its name, and verify “I'm not sure” and hazard conditions still prevent an unverified cleaner being used. Confirm a saved unreviewed Arsenal item can be selected only as the player's own, explicitly unapproved method.

**The Chromium integration suite does not replace this check.** Record device model, OS version, browser, installed-versus-tab mode, date, deployed Git commit and pass/fail for each item. Avoid recording personal images, addresses, product secrets or other sensitive content.

Test origin: [GrimeQuest HTTPS](https://grimequest-web-production.up.railway.app/). Production defaults to **real, private, self-reported guided camera quests**, with a separate practice tutorial. Public model-based AI comparison remains disabled unless a controlled provider preflight passes.

## Installed app update/recovery (required before accepting photo-limit fix)
1. Install the previous build with its old cache-first worker, open the app and verify original local inventory survives page reload.
2. Publish the new build. Reopen the installed Home Screen app while online; the new worker must precache completely before activating. If an update arrives during a live task, no automatic reload may interrupt it.
3. If stale assets persist, open **Settings → Refresh or repair this installation**, tap **Refresh installed app**, and verify that the previous 12-MP warning no longer exists in the current app. Verify saved inventory and journal survive (do not record photos).
4. Verify /update.html, /update.js and /update.css respond with `Cache-Control: no-store` and are excluded from all service-worker cache allowlists, including the prior release's list; QR and offline shell remain functional.
5. Repeat from a real iPhone Home Screen app context; testing only a Safari tab is insufficient because installed web apps have separate storage. Test offline after recovery and ensure the worker is registered again.

## Offline practice and install (no AI required)

1. On a computer, open the HTTPS home page: confirm the game is immediately playable without an install gate. Select **Use on phone** in the footer, then verify the opt-in QR code links to the same-origin HTTPS root without third-party requests, and that **Continue in desktop browser** restores the game. Then open that HTTPS URL in iPhone Safari 17+ and a current Android Chrome browser if both are available. Confirm the page renders without horizontal scrolling at normal display scale.
2. Scan the desktop QR with the real phone camera and accept the URL banner. On iPhone tap **Share → Add to Home Screen** (enable **Open as Web App** when offered) / on Android Chrome use **Install app** when available. Open it from the icon; verify standalone display and app icon. Also test a browser without install-prompt support: the manual guidance must remain available.
3. Complete one **Practice** Grease Gremlin clear and one deliberately **unverifiable/partial** outcome. Confirm only clear yields practice XP, and that the journal labels the results **SIMULATED**.
4. Reload the page, switch tabs and reopen the installed app. Confirm inventory and practice journal persist, no duplicated clear XP appears, and interrupted live tasks cannot be silently forgotten.
5. While online, visit privacy and safety notices; then go offline and reopen the installed shell. Confirm practice/history remain available while live analysis explicitly reports that the network is required.
6. Turn on text enlargement, VoiceOver or TalkBack where available. Confirm focus labels, touch targets, error messages, choice groups and the ability to operate without visual animation.

## Local camera/file test (private testing only)

Camera analysis requires a separately authorized, private live configuration. The supported production URL must not have public AI enabled before the real safety evaluation. When an operator sets up a **private** test origin and access code:

1. Tap **Live camera**, grant camera access when prompted; confirm an actual rear-camera preview appears. Deny permission and ensure file-picker fallback and an explanatory message remain available.
2. Capture one ordinary, cool, unpowered, non-sensitive target. Confirm that the image is normalized locally to JPEG and that a separate explicit consent control appears **before** any upload.
3. Test file-picker alternatives: JPEG, PNG, WebP and an actual iPhone HEIC/HEIF photo. **Specifically test unmodified 24/48 MP phone target photos larger than 8 MB**, and a normal barcode photo for local barcode decoding. Front/back label OCR is retired from player use. Verify they are accepted, resized locally to at most 1600 pixels per edge, remain correctly oriented and keep label text legible, with no upload before explicit consent. Safari 17+ can decode HEIC natively. On browsers without native HEIC decoding, confirm a specific **export JPEG** message appears. Unsupported SVG/RAW is rejected. Source files over 100 MB may still require an ordinary JPEG/HEIC export.
4. For the selected photo, test landscape/portrait rotation and background/resume. Confirm active camera tracks shut down on cancel, navigation, pagehide and document hidden. No camera stream should persist after leaving capture.
5. Reject upload consent and verify **no server/provider call** and no award occurs. Accept consent only after reviewing the configured image provider's privacy terms.
6. Test one deliberately uncertain material or unsupported cleaner. Confirm it cannot progress to a recommended chemical through a model guess or scanned bottle label alone.
7. For a real cleaning comparison, follow **exact current physical bottle and material instructions**, do not mix products, never use heat/electrical hazards, and separately assess visible **clear**, **partial**, **unchanged** and **unverifiable** cases. No disinfection claims.
8. Verify that duplicate after-photo requests do not award repeated live XP and that network outage/timeouts never substitute a practice-mode result as real AI.

## Evidence / sign-off

Record results in a private test sheet, not the public GitHub repository. Include only case IDs, device/browser details, app commit, timestamp, outcome and sanitized technical errors; do not attach unredacted photos.

**Go/no-go:** the release remains `NOT_READY_FOR_GENERAL_PUBLIC_LIVE_AI` if any real-model false clear or false supported recommendation, missing privacy consent, camera leakage, image-decoding crash, or absent provider/privacy owner detail remains. The owner keeps the repo private until explicit final publication approval.

## Historical, operator-only Google Cloud Vision OCR validation (not required for barcode-first judging)

1. Without the operator's restricted Google Vision key, the UI must offer **manual product entry**, not suggest that users configure a server. The rest of the camera quest stays playable.
2. Enable the Vision API in a dedicated, billed and quota-controlled Google Cloud project, restrict the API key to that API and connect it only in Railway. Verify health advertises `label_ocr_ready=true` only after explicit operator activation.
3. Scan front/back labels with normal high-resolution iPhone photos and clear Finnish/English product text. Explicitly approve the third-party Google Vision image-processing checkbox; declining must result in **zero Cloud Vision requests**. Confirm the Vision API only sees metadata-stripped images and one TEXT_DETECTION plus one DOCUMENT_TEXT_DETECTION feature.
4. Confirm returned text is editable, names like `| MTT` are never silently saved as product names, warnings are treated as potentially incomplete and an explicit label-review confirmation is mandatory. No scan or saved note grants cleaning-product compatibility.
5. Test an invalid Google key, provider timeout, rate/quota exhaustion, image upload failure and provider errors. Photos and manual drafts must remain editable; no automatic retry or switch to paid OpenRouter inference.
6. Compare recognized results against actual bottles and record measured name and warning accuracy. Mock-only protocol verification is not evidence of real OCR accuracy.


## Barcode-first product entry (replaces label OCR)

1. On actual iPhone Safari Home Screen PWA, choose **Arsenal → Scan barcode**. Confirm the camera opens only on tapping, the locally bundled ZXing reader detects EAN-13, and the video tracks are stopped on success, cancellation, navigation, backgrounding or app switch. Photos and camera frames are never sent to the backend.
2. Scan a clean printed code from a household product and confirm lookup starts **automatically** after decoding. Only GTIN digits may leave the device for Open Facts, UPCitemdb and EAN-Suche, with optional operator-enabled Serper fallback after structured catalogs miss. Check response name/brand/size against the physical bottle, and require explicit confirmation of a community suggestion before saving.
3. A valid barcode absent from the community index, an offline phone, or a 429/503 lookup outage must still allow manual product name entry and save as unreviewed without a photo or third-party data request.
4. Verify typing a valid EAN/UPC/GTIN works even when camera access is denied or no library loads. Wrong check digits are rejected. Manually entered product records with no barcode and existing inventory records must remain readable and exportable.
5. Verify Finnish cleaner GTIN coverage against real bottles; record hit rate and do not assume Open Products Facts has every SKU. A found name never grants chemical/surface compatibility. Keep manufacturer label and surface-care instructions authoritative.
6. Confirm no product-label OCR controls, Google Vision photo consent or provider key configuration are shown to players; the operator-disabled Google OCR service is not called in the barcode flow.

## Worldwide product discovery acceptance (cross-country testing)

1. Search by brand/name in both Latin and non-Latin scripts, including a Japanese/Arabic/Cyrillic product. Check that typed text is sent **only after** tapping Search and that no camera frame or photo reaches the external community search. There is no Finnish- or UK-only filter.
2. Confirm per-result source attribution and product category across Open Products Facts, Open Beauty Facts, Open Food Facts and Open Pet Food Facts. Verify exact GTIN/name/brand/quantity against physical packaging. A source match cannot unlock chemical-use eligibility.
3. Test global barcode fallthrough: if the general-products index lacks a GTIN, a match in cosmetics, foods or pet foods may be suggested. No external redirects to unreviewed hosts or provider text interpreted as cleaning instructions.
4. Verify no source match, 429 throttling, 503 upstream error, offline mode and wrong search input all allow manual product entry without camera, provider keys or purchases. Results from search must remain unreviewed until a user explicitly confirms the exact variant.
5. Measure actual lookup hit rates on internationally distributed household products **before** claiming global database coverage. Record country/product category and match/mismatch rates; none of the mocked API tests certify full global coverage.
6. Check accessibility/keyboard operation of search results at 320 px mobile width, source-link safety, photo privacy and compatibility with older browser local inventory records.
