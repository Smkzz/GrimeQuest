# GrimeQuest

## Your mess. Their problem.

**Turn one real chore into a tiny monster battle.** Photograph a dirty spot, clean at your own pace, and evict the little freeloader living there.

**[Play GrimeQuest](https://grimequest-web-production.up.railway.app/)** · No account · No uploads · No setup

Not near a mess? The **15-second illustrated demo** shows the entire idea immediately. Demo play never awards points or changes your collection.

### Find. Clean. Defeat.

1. **Find some grime.** Take a before photo or choose one from your device. No material forms, cleaner database, shopping list or AI wait.
2. **Evict your opponent.** A fictional grime creature moves into your before photo. Clean the real spot using the proper care instructions you already have. No timer or pressure to clean more.
3. **Enjoy the difference.** Take an after photo, confirm your own result, slide between before and after, and collect **300 XP** and a creature for your collection.

Meet **Smudgie, Dusty, Crumb Goblin, Splodge, Grubble and Lord Grime**. They have personalities and original SVG artwork, not chemical advice. Complete six little chores to meet the whole crew. Every three completed quests advances a level. A repeated claim for one quest cannot award duplicate XP.

### Small enough to actually use

The primary flow remains three steps. Camera/file fallback, retake, a before-photo alignment guide, in-session quest recovery and a keyboard-operable comparison slider support the chore rather than complicating it. Installation and text-only sharing are optional. Reduced-motion preferences disable creature and celebration animations. Existing local guided XP is retained; old quests do not fabricate monster encounters.

### What the app honestly knows

**The monsters are make-believe. Your progress is self-reported. The chore is real.**

GrimeQuest does not recognize dirt or materials, recommend chemicals, verify that you cleaned, or measure hygiene/disinfection. The character is selected by game progression, not image recognition. The after-photo confirmation records your own assessment. Identical before/after photos are rejected, but this is not anti-cheat or proof of cleanliness.

Follow the actual product label and the object's care instructions. Never mix or layer cleaners. Skip unsafe, damaged, powered/hot or uncertain targets. The game is motivation, not a cleaning-safety authority.

### Private by design

Your before/after photos stay in browser memory and are **not uploaded by the game**. Completed wins and XP are stored locally without an account or analytics. Sharing a win sends only text and the app link, never the photos. The illustrated demo uses original local SVG scenes, not someone else's private pictures.

Unfinished photos survive navigation inside the app but are lost if the tab closes or reloads. The app warns before leaving an unfinished real quest where the browser supports that warning. Completed history persists unless browser storage is cleared or unavailable. Up to 200 recent entries are kept; this is not a permanent or verified leaderboard.

The installable PWA works offline after its complete shell has been cached. On iPhone, use Safari → Share → Add to Home Screen, or the app's **Install / share** guide. The first visit is never blocked by an installation screen.

### Development and qualification

The repository contains the current casual UI plus isolated legacy backend/catalog tests. Product-search and AI APIs are not used by the public monster game. No runtime AI provider, API key or paid model call is required to complete it.

The reproducible Docker paths install pinned dependencies, bundle the assets, compile strict TypeScript and run checks:

```sh
# Full Python, Node, Chromium and real-origin PWA qualification
# Includes historical backend contracts and the public monster-game tests.
docker build -f Dockerfile.qualify -t grimequest-qa .

# Production image: tested static PWA + same-origin API host
docker build -t grimequest .
docker run --rm -p 8080:8080 -e PORT=8080 grimequest
```

Open `http://localhost:8080`. Production is deployed over HTTPS on Railway. GitHub Actions are manual-only; automated qualification does not require paid AI inference.

The public UI is in `client/casual.ts`, the deterministic collection and original art in `client/creatures.ts`, and the responsive skin in `web/game.css`. `tests/test_monster_game.py` covers demo isolation, six-creature progression, sharing privacy, accessible before/after comparison, alignment, reduced motion and quest recovery.

### Launch material

- [Submission copy and real-task video script](docs/MONSTER_SUBMISSION_20261009.md)
- [Original casual iPhone acceptance checklist](docs/CASUAL_PHONE_ACCEPTANCE_20261008.md): still applies to the camera, offline and local-history paths; additionally test the demo and comparison slider.
- [Privacy](PRIVACY.md) · [Safety](docs/SAFETY.md) · [Third-party notices](THIRD_PARTY_NOTICES.md)

**Actual iPhone/Safari hardware acceptance remains a separate check.** Chromium automation and an illustrated demo cannot establish native HEIC camera behavior or prove real-world cleaning.

Built for the international Hackyard gamification challenge. Original source and artwork are MIT-licensed; see [LICENSE](LICENSE). No manufacturer endorsement or chemical-safety certification is implied.
