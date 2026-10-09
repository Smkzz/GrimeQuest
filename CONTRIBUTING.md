# Contributing to GrimeQuest

Thanks for helping make a tiny real-world chore more enjoyable. GrimeQuest is a **privacy-first, self-reported gamification PWA**, not a cleaning-safety authority or AI dirt-recognition service.

## Before proposing a change

- Search existing issues and pull requests. Start a focused issue for substantial gameplay, security or API changes.
- Work on a branch and send a pull request to **main**. Keep changes small, especially near releases.
- Use synthetic illustrations or redacted examples, never private household photos, addresses, real product labels, credentials, private evaluation datasets or local evidence.
- Do not claim fictional monsters are photo analysis or that XP proves actual cleaning.

## Local development

Install Node 22+, Python 3.13+ and Playwright/Chromium support, then run:

    python -m pip install -r requirements-dev.lock
    npm ci --ignore-scripts
    python scripts/build.py
    npm run typecheck
    npm test
    python -m playwright install chromium
    python -m pytest --cov=server --cov-fail-under=90
    python scripts/verify_build.py

Alternatively use the pinned Docker qualification image described in
[RELEASING](docs/RELEASING.md). Do not make billable provider requests or
trigger hosted CI without explicit budget authorization. GitHub Actions are
deliberately manual-only.

## Special review rules

- **XP:** one self-reported 300-XP win per valid completed quest; no duplicate
  award or unearned simulated/demo reward.
- **Demo:** no API calls, actual camera requirement, XP or collection mutation.
- **Photos:** keep them local and temporary. No image bytes in local history,
  sharing payloads, remote analytics or public fixtures.
- **Camera/PWA:** clean up media tracks, preserve saved history and test
  interrupted-task recovery and offline shell updates.
- **Accessibility:** check keyboard focus, native slider operation, alternative
  photo selection, reduced motion and small viewports.
- **Chemical policy:** the old product/API code is retained for compatibility,
  not part of the public game. Any change to chemical advice or server
  permissions requires a separate safety and evidence review.
- **Licenses:** document third-party dependencies and the provenance of art.

Every PR should describe user-visible behavior, privacy/safety implications,
what was tested, what was not tested and any new release risks. See the
[code of conduct](CODE_OF_CONDUCT.md), [support guide](SUPPORT.md) and
[release guide](docs/RELEASING.md). Security issues should be reported through
[SECURITY.md](SECURITY.md), not public issues.
