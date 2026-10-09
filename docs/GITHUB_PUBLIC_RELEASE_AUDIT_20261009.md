# Public GitHub release-readiness audit — October 9, 2026

## Scope and outcome

The canonical public GitHub repository is
[Smkzz/GrimeQuest](https://github.com/Smkzz/GrimeQuest).
The application served by Railway is a local-photo,
**self-reported**, fictional grime-monster game.

**Software release-artifact qualification passed.** This is a substantive
open-source and packaging review, **not a blanket 10/10 certification**.
The site does not provide AI-backed cleaning inspection, hygiene proof,
chemical recommendations, cloud history or user accounts.

## Evidence collected

- GitHub API confirms repository visibility **public**, detected **MIT**
  license and canonical source path.
- The repo has a README, pinned dependency manifests, strict TypeScript,
  automated tests, Docker and isolated QA builds, SECURITY,
  CONTRIBUTING, THIRD_PARTY_NOTICES, a manually triggered CI workflow,
  and Dependabot update configuration.
- Public tracked source was scanned with credential-like and private-path
  heuristics. No apparent live credentials were identified by those checks.
  This is **not** a full Git-history, entropy, provider or repository-host
  secret scan; owners should enable GitHub secret scanning/push protection
  and rotate any credential ever exposed in history.
- A clean-room Railway qualifier on source
  **7943bccbb65b7231977bc1b15f22a9d467fe01f9** ran
  **540/540 Python/API/Chromium/real-origin PWA tests** and
  **61/61 Node tests**: **601 passed, zero failed**.
  The new release packager's six tests validate inclusion of only tracked
  files, SHA-256 readback, stable bytes, dirty-tree refusal, secret rejection,
  private-evidence refusal, path/symlink safety, version parity and
  required docs.
- Python combined branch/line coverage on the retained backend was
  **90.43%** in the current QA baseline; 252 non-failing warnings remain,
  mostly FastAPI lifecycle deprecations. TypeScript 5.8.3 compiled and
  the generated PWA was byte-identical on rebuild.
- This isolated QA does not perform paid model calls. The owner budget
  preference is respected: hosted GitHub Actions remain manual-only.
  A healthy Railway run is not a CodeQL analysis or a GitHub Actions run.
- README and important project docs now link to the canonical owner,
  provide current monster-game release notes, and clearly distinguish
  historical AI/barcode prototype reports.

## Findings remediated on the release branch

| Original issue | Change |
| --- | --- |
| ZIP packager recursively included untracked local files and optional evidence media | Replaced with fail-closed Git-index-only source packaging; no local screenshots, .env, evaluation outputs or private evidence |
| Release manifest hard-coded October 6 and an old prototype claim | Manifest now uses full checked Git SHA, commit timestamp, pinned version and per-file SHA-256 |
| Missing current release guidance | Added RELEASING with exact-source, tag, checksum, draft/publication and submission steps |
| Current release omitted from changelog | Added truthful v0.1.0 monster-game notes; older AI/product work retained as labeled historical notes |
| Bug template referenced retired Practice/Live UI | Now offers real quest, demo, camera/HEIC, collection, accessibility, PWA, build and legacy API |
| Contribution guide centered on historical chemical workflow | Replaced with present-game, privacy, QA, accessibility and self-report guidance |
| Code of conduct, support and accessibility guides absent | Added; avoided fictional response guarantees, security contact addresses or false WCAG certifications |
| Vulnerability policy lacked a public reporting path | Added conditional private GitHub advisory guidance; owner still must enable and verify its availability |
| Some docs linked to the old organization slug and asserted the repo was private | Updated current links to Smkzz/GrimeQuest and corrected public status |
| Historical architecture/release evidence looked like the current player interface | Added prominent historical markers and a documentation index |
| No release-note category template | Added optional .github/release.yml; this creates no automatic release or hosted run |
| Manual CI did not verify safe release packaging | Added a ZIP/checksum step, still opt-in/manual-only |

## Outstanding owner-controlled GitHub settings

The current repository metadata was directly observed to have:
**no description, no homepage, and no topics**. The release API returned
**zero published releases**, and the ruleset API returned **zero rulesets**.
The connected tool does not expose repository About editing or GitHub
Release publishing; these steps remain manual.

For the **About** section:
- Description: **A tiny cleaning game: snap the grime, defeat a monster,
  earn XP and collect the crew. Private, no accounts or AI required.**
- Website: **https://grimequest-web-production.up.railway.app/**
- Suggested topics: **gamification, pwa, typescript, python, cleaning,
  hackathon, offline-first, open-source**

Follow [RELEASING](RELEASING.md) to create a **draft GitHub v0.1.0 Release**
for the exact qualified deployed commit, inspect the generated notes/optional
safe ZIP, and publish it once manually checked.

The private vulnerability-reporting, secret scanning and push-protection
settings were **not directly verifiable** with the connected repository
permissions. Enable and verify available options through GitHub Settings.
After the event, add appropriately tested main/production branch rules
without accidentally interrupting the authorized Railway deploy.
The hosted CodeQL/Actions run status is **not qualified**; do not represent
it as performed. Contributor moderation has no verified private email.

## Critical event and real-world boundaries

Hackyard's rules allow pre-kickoff planning but not the builder's own
pre-written project code. GrimeQuest ideation/exploratory work began
before the October 5 kickoff. The exact quantity of pre-window source
was not independently reconstructed and must **not** be misrepresented
or concealed; see [HACKATHON_PROVENANCE](HACKATHON_PROVENANCE.md).

A real iPhone/Safari/HEIC capture and an actual completed safe chore are
outside what these automated tests prove. The repository's privacy policy
still needs finalized operator/contact details for a broader public service.

This review cannot guarantee a contest win, independent security
certification, WCAG compliance, full historical secret scanning, exact
GitHub branch settings or real cleaning effectiveness.

## Ship decision

**GO** for merging verified repository hygiene/packaging changes once
the final candidate build finishes successfully. Require the exact
Railway-watched production commit to become healthy after fast-forward.
Remove temporary QA services when safe.

**NOT YET COMPLETE:** a published GitHub Release/tag, optional About
metadata, verified security settings, independently completed hardware
acceptance, and actual Hackyard submission. Those require owner action
and should not be silently counted as passed.
