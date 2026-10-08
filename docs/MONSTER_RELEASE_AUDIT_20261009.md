# GrimeQuest monster release audit — October 9, 2026

## Product decision

Keep the no-setup camera loop and add one coherent reason to remember it: **a real small chore becomes a fictional monster eviction**. No surface/cleaner selection, mandatory account, runtime AI, public leaderboard, timer or external service was added to the player journey.

The release adds six original SVG characters with names and taunts; a separate illustrated try-now demo; a camera alignment overlay; keyboard-operable before/after reveal; optional reduced-motion celebration; collection unlocks and level progress derived from real-mode self-reported wins; and user-initiated text-only sharing. Photos remain on the device.

## Qualified functional candidate

- Repository: `Smkz-Entertainment/GrimeQuest`
- Functional source: `456251a387f8369b03afc22a4308303b20c0a625`
- Branch: `launch/grime-monsters-20261009`
- Separate Railway qualification deployment: `338ff5b2-ffba-49af-9171-de66e5752d99`
- Qualification Dockerfile: `Dockerfile.qualify`
- Environment: pinned production-family Python 3.13, Node 22, real Chromium; no paid inference calls
- Deployment/build status: **SUCCESS**

| Gate | Observed result |
| --- | --- |
| Strict TypeScript | PASS |
| Node domain, camera, storage and app-shell tests | 61 passed |
| Python/API/Chromium/browser/real-origin PWA tests | 534 passed |
| Total automated tests | **595 passed, zero failed** |
| Python combined statement/branch coverage | **90.43%**, above the 90% gate |
| Warnings | 252 non-failing warnings, mainly retained FastAPI lifecycle deprecations |
| External AI inference | Zero calls in qualification |
| Real phone hardware | **Not independently observed** |

The first full run found one duplicated Resume control when opening the collection during an unfinished quest. The UI was corrected to keep one clear resume action; the existing regression assertion was not weakened. The subsequent full suite passed. Additions after the qualified functional source are submission/audit documentation and privacy-notice copy, not gameplay logic.

The older test suites include historical backend/catalog compatibility checks. The full count is not a claim that every test targets the new public UI. `tests/test_monster_game.py` specifically exercises the newly shipped mechanics.

## Critical behavior verified

- The illustrated demo can be repeated without camera/API calls, XP, wins, collection unlocks or changes to saved progress.
- Real-mode wins require a before photo, an after photo and an explicit player claim; identical image data is rejected.
- One claim cannot be applied twice to the same quest. XP remains fixed at 300 and uses `self_attested`, never AI-verified provenance.
- All six creatures unlock through separate recorded real-mode quests; old guided points, practice, AI and partial results do not invent collected creatures.
- The reveal supports keyboard operation and changes only the displayed split; original image bytes remain unchanged.
- The camera alignment guide is a DOM overlay, not a modification to the image or alleged AI guidance.
- Share is explicit and contains exactly title/text/app URL, not photos or files. Its text says self-reported.
- A quest and its after photo survive navigation to My wins and Settings. Discard requires confirmation, with keyboard Escape preserving the quest.
- Reduced-motion mode disables character and confetti animations.
- Public flow and illustrated demo fit the tested 320-, 390- and desktop-width Chromium viewports without horizontal overflow.
- The monster skin is included in the offline shell and inlined in the standalone artifact rather than relying on a CDN.

## Visual review

Desktop and 390/320-pixel screenshots of the shipped game components were rendered in an isolated local visual harness. They cover home, illustrated battle, illustrated result and empty collection. The harness is not a substitute for the actual deployed server or physical cleaning. All illustrated scenes remain labeled as such.

## What this audit does not establish

It does not guarantee a hackathon win, objective 10/10 usability, native iPhone/HEIC/PWA behavior, a real cleaning outcome, hygiene, chemical suitability, a security penetration test or legal compliance. Runtime gameplay does not perform AI analysis. Completed history is local, user-editable and limited to 200 entries; it is not an anti-cheat system or permanent cloud account.

Before submitting, physically test one safe before → clean → after → XP → collection journey on the actual iPhone, inspect the comparison slider and reduced-motion behavior, and try the illustrated demo without earning points. The operator also needs to review privacy-contact details and public-source contents, publish the currently private repository deliberately, complete the model declaration, and actually submit the entry.

## Release acceptance

Merge only after reviewing the exact candidate, fast-forward the Railway-watched `production` branch, require the production Docker smoke and `/api/health` checks to succeed on that merged SHA, then remove the temporary qualification service. Keep the final hours for physical acceptance, a truthful real-chore video and submission rather than another architecture change.
