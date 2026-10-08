# GrimeQuest casual release — 10-minute iPhone acceptance

**Test the current deployed SHA.** Browser automation does not substitute for a real iPhone camera or the installed Home Screen PWA.

Record in private notes: phone model, iOS version, Safari/PWA mode, time, app commit, each pass/fail, and a sanitized error (no personal photos).

## Mandatory user journey

- [ ] Open the public HTTPS link on iPhone in Safari. A casual home page says **A little mess. Big little win.** with one main **Find some grime** button. No account, product name, barcode or surface-selection screen appears.
- [ ] On an older installed PWA, finish any ongoing task, open **Settings (⋯) → Refresh the installed app**, and complete the safe refresh. Existing XP and old inventory must remain unless the user deletes them.
- [ ] Tap **Find some grime**. Grant camera permission; check real rear-camera preview. Camera starts only after the tap. Deny permission on a separate test and use **Choose photo** instead. Take a normal real before photo, including an iPhone HEIC/HEIF image when available.
- [ ] **Take photo** is not clickable until video is ready. Retake works. Use **Let’s clean!** and verify the app moves directly to **Time to clean!** with no material or chemical choice.
- [ ] Perform a real, safe household cleaning chore using the object's proper care instructions and the current product label. GrimeQuest must make **no product or surface compatibility recommendation** and should never encourage mixing or speeding up chemical steps.
- [ ] Tap **Done cleaning**, capture the same dry target from a comparable angle, and tap **It’s clean! +300 XP**. Result clearly says **Self-reported** and shows both photos.
- [ ] Open **My wins**. Verify +300 guided XP, a single new history row, and no duplicate points if you revisit the result. Close/reopen PWA; XP/history should remain; photos must not appear in browser localStorage.
- [ ] Test using the **exact same** before/after photo: XP must stay unchanged with a clear message. Test Cancel and Back to cleaning without mistakenly awarding points.
- [ ] Switch phone to airplane mode **after** a full PWA precache, reopen it and repeat the photo/photo/XP journey. No model, API key, account or connection is required.
- [ ] Confirm the UI fits in narrow portrait mode without horizontal scrolling, the bottom action buttons work with the virtual keyboard, VoiceOver focus labels are usable, and camera tracks stop when navigating away or backgrounding.
- [ ] On desktop, opening the link starts the game immediately. The optional **Install / share** link shows the QR handoff; clicking **Continue in desktop browser** returns to the game.

## Launch blockers to record, not conceal

- A device-specific HEIC decode, rear-camera, Safari Home Screen PWA, service-worker update or touch issue.
- Any unexpected photo upload, user credential requirement, chemical recommendation or product/surface selection in the default casual game.
- Any XP awarded for an identical photo or without the player's explicit **It’s clean!** action.
- Private GitHub repository, missing public live link, missing actual real-task demo video, or hackathon submission left in draft.

The browser build and isolated Chrome/Playwright tests check software behavior, not actual household cleanliness. Keep all claims explicitly **self-reported**.
