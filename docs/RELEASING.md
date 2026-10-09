# Releasing GrimeQuest on GitHub

Current canonical source: [Smkzz/GrimeQuest](https://github.com/Smkzz/GrimeQuest). Deployed PWA: [Play GrimeQuest](https://grimequest-web-production.up.railway.app/).

**The monsters are fictional. All results are self-reported.** Neither the game nor the illustrated demo recognizes chemicals, verifies hygiene, or certifies that cleaning happened.

## 1. Tag and source identity

- **main** is the reviewed source; Railway deploys **production**. Before a release, verify which exact commit is deployed and confirm both branches agree.
- The release version in **package.json** must match **pyproject.toml**. Initial planned public release: **v0.1.0**.
- Release tags should identify a specific tested commit. Do not tag one SHA while publishing build evidence from another.
- Real iPhone/Safari/HEIC, installed-PWA and physical cleaning still require human acceptance. Chromium tests cannot certify them.

## 2. Qualify the source

On a clean checkout of the canonical public repository:

    git clone https://github.com/Smkzz/GrimeQuest.git
    cd GrimeQuest
    git checkout main
    git status --short
    git rev-parse HEAD
    python -m pip install -r requirements-dev.lock
    npm ci --ignore-scripts
    python scripts/build.py
    npm run typecheck
    npm test
    python -m playwright install chromium
    python -m pytest --cov=server --cov-fail-under=90
    python scripts/verify_build.py

Or build the pinned Python/Node/Chromium clean-room image:

    docker build --pull -f Dockerfile.qualify -t grimequest-qa .

Neither procedure requires paid runtime inference. The GitHub Actions workflow is intentionally **manual-only** because the owner has a zero-paid-CI budget. Railway qualification is not evidence that GitHub Actions or CodeQL ran.

## 3. Fail-closed source package

Only make a public archive from a clean, indexed Git checkout:

    python scripts/package_release.py

The packager refuses a dirty tracked tree, missing Git identity, mismatched versions, unsafe symlinks, recognized credentials, tracked private evidence paths and oversized files. It includes **only Git-tracked files**, writes an embedded file-by-file SHA-256 manifest with full commit SHA and commit date, verifies the ZIP by readback, and emits a companion checksum file in the checkout's parent directory.

Untracked files, real household pictures, local evidence and private evaluation data are **not included**. Do not manually zip your developer checkout or attach unredacted evaluation screenshots. Review historical Git commits for credentials; if a secret was ever committed, **revoke or rotate it** even if a later commit removed it.

GitHub automatically provides source archives for each release tag. The generated ZIP and checksum are optional downloadable convenience artifacts.

## 4. Draft the GitHub Release

Follow [GitHub's official release documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository):

1. Open **Releases → Draft a new release** on the canonical repo.
2. Choose **Create new tag v0.1.0** and target the exact, successfully qualified and deployed commit.
3. Title: **GrimeQuest v0.1.0 — Your mess. Their problem.**
4. Use the v0.1.0 section of **CHANGELOG.md** and the release description below. Do not claim AI-verified cleaning.
5. Optionally attach the ZIP and matching SHA-256 file produced from the same clean source commit.
6. Preview and **Publish release**, then verify the public release, tag, source archives, license, and demo link from a logged-out browser.

Suggested release description:

> **Your mess. Their problem.** Turn a small real-world chore into a tiny monster battle. Snap the dirt, clean at your own pace, compare the before/after images, and evict one of six original collectible grime monsters. Includes a separate illustrated zero-XP demo, levels, local collection, and optional text-only sharing. No accounts, cloud photo uploads, product selection or runtime AI.
>
> **Limitations:** Cleaning is self-reported and does not verify hygiene or product safety. Always follow real care/label instructions. Progress is stored on-device. Physical phone-camera behavior must be tested independently.

The connected repository tool may not expose GitHub Release publishing. If so, publishing the tag and GitHub Release remains a manual owner step; a release document is **not** a published release.

## 5. Community and security settings

[GitHub's community profile checklist](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories) includes README, LICENSE, SECURITY, CONTRIBUTING, CODE_OF_CONDUCT and valid issue forms. SUPPORT and ACCESSIBILITY documentation give users clear reporting paths. Their presence does not certify product quality.

From **Settings → Security / Advanced Security**, review Dependabot alerts, secret scanning, push protection, CodeQL availability, and private vulnerability reporting. Use [GitHub's security quickstart](https://docs.github.com/en/code-security/getting-started/quickstart-for-securing-your-repository). Do not claim these switches are enabled until observed. CodeQL or hosted workflows can have plan-dependent usage and costs; do not turn them on automatically with a zero-paid-CI budget.

After the contest, consider a ruleset requiring PR review and validated checks before merging to main and production. Do not add rules that unexpectedly block the current authorized Railway deploy.

## 6. Hackyard submission is a separate action

[Hackyard Yard #4](https://hackyard.tech/schedule) ships **Friday, October 9, 2026 at 18:00 UTC / 21:00 Finnish time**.

- [ ] Public source URL is the canonical Smkzz/GrimeQuest repository.
- [ ] Latest production HTTPS build works for logged-out visitors.
- [ ] Writeup is within the permitted character limit and accurately describes the self-reported game.
- [ ] AI model declaration includes the build models used, not just the runtime (which uses no model).
- [ ] Optional screenshot/video show the true UI, with real cleaning clearly distinguished from the illustrated demo.
- [ ] If published, the GitHub Release/tag/attachment refers to the exact qualified commit.
- [ ] The entry is actually **submitted**, not just saved as a draft. Keep private confirmation.

A public repository and healthy deployment **do not automatically submit** a hackathon entry.
