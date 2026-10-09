# GrimeQuest documentation guide

**Current product:** a playful, self-reported, on-device camera game. Photograph
one dirty spot, safely clean it, compare photos, and evict a fictional monster.
The public player experience does **not** ask for a cleaner, material or AI key.

## Current and authoritative for this release

- [Public README](../README.md) — what the app does, how to play and build.
- [Releasing on GitHub](RELEASING.md) — safe Git-tracked source archive,
  checksums, tag/release procedure and security/CI caveats.
- [Monster-release audit](MONSTER_RELEASE_AUDIT_20261009.md) —
  separately qualified functional build and limitations.
- [Physical iPhone checklist](CASUAL_PHONE_ACCEPTANCE_20261008.md) —
  real capture/HEIC/offline/XP acceptance still requires the actual phone.
- [Short real-chore demo script](DEMO_SCRIPT.md) —
  no fake cleaning or misleading hygiene claims.
- [Hackyard submission kit](MONSTER_SUBMISSION_20261009.md) —
  writeup, optional video, exact source link and required model declaration.
- [Source-timing provenance](HACKATHON_PROVENANCE.md) —
  distinguishes pre-event ideation from permitted in-window code.
- [Privacy](../PRIVACY.md), [Security](../SECURITY.md),
  [Support](../SUPPORT.md), [Accessibility](../ACCESSIBILITY.md),
  and [Third-party notices](../THIRD_PARTY_NOTICES.md).

## Historical prototype documentation, not the current player flow

Earlier GrimeQuest explored AI target/label reading, international product
lookups, source-reviewed cleaning-label matches, paid-provider spending gates
and more complex guided task screens. The implementation remains separated
in guarded legacy code for backwards compatibility and regression tests.

The following files are **development history**, not instructions that
players should follow to start the present game:

- [Original architecture](ARCHITECTURE.md), [build plan](BUILD_PLAN.md),
  [original release gates](RELEASE_GATES.md), [hosted status](HOSTED_STATUS.md),
  and [historical test report](TEST_REPORT.md).
- [Google Vision setup](GOOGLE_CLOUD_VISION_SETUP.md),
  [paid vision precheck](PAID_VISION_PRECHECK.md),
  [provider evaluation](PROVIDER_EVALUATION.md),
  [real provider smoke](REAL_PROVIDER_SMOKE_20261008.md),
  and [ZDR trial](REAL_FIXED_ZDR_TRIAL_20261008.md).
- [Reviewed product catalog](PRODUCT_CATALOG_REVIEW_20261008.md),
  [original phone release checklist](PHONE_RELEASE_CHECKLIST.md),
  [legacy safety evidence](SAFETY.md),
  [October 8 casual audit](CASUAL_RELEASE_AUDIT_20261008.md)
  and [earlier launch review](FINAL_LAUNCH_AUDIT_20261008.md).

Historical report dates and test counts must not be presented as the latest
quality result. The current game never identifies a cleaning chemical,
measures hygiene or awards demo XP.

For a reported security vulnerability, use the private reporting guidance
in [SECURITY.md](../SECURITY.md), not a public issue containing secrets or
photos.
