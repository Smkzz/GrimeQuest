# GrimeQuest v0.1.0 — release-candidate qualification report

**Date:** 2026-10-07  
**Verdict:** Application code, deterministic policy, PWA delivery, security boundaries and the hosted protocol qualify under automated/clean-room testing. **Real vision-model accuracy, physical cleaning and target-phone hardware behavior remain unqualified.**

## Final automated baseline

| Check | Observed result |
| --- | --- |
| Python/API/policy/image/provider/browser/evaluation tests | **412 passed, 0 failed, 0 skipped** |
| TypeScript-domain / storage / camera / service-worker Node tests | **34 passed, 0 failed** |
| Total automated test cases | **446 / 446 passed** |
| Client/server policy parity | **1,680 combinations agree** |
| Strict TypeScript | **5.8.3 — pass** |
| Clean-room Python | **3.13.16** |
| Clean-room Node | **22.23.3** |
| Python combined line/branch coverage | **97.76%** |
| Provider adapter measured coverage | **100%** |
| Generated PWA rebuild | **Byte-identical** |
| npm clean-install audit | **0 vulnerabilities** |
| Full OSV exact-version audit | **32 checked, 0 vulnerable, 0 errors** |
| Hosted public-HTTPS protocol qualification | **PASS with deterministic observation fixture** |
| Real/paid provider calls | **0** |
| GitHub Actions automatically consumed | **0** |
| Base-image / effective-runtime Trivy scan | **Effective runtime equivalence passed: 0 HIGH/CRITICAL after removing unused tooling.** An exact final registry-artifact scan is still outstanding. |

## Clean-room qualification

A disposable Railway service builds `Dockerfile.qualify` from the repository source. It uses the same digest-pinned Python 3.13 base family as production, adds pinned Node 22 plus system Chromium, performs a clean Python/npm install, runs `pip check`, compiles the PWA, runs strict TypeScript, all 34 Node/client tests, all 412 Python/API/browser/evaluation tests with coverage, and `scripts/verify_build.py`.

The accepted clean-room build emitted:

```text
412 passed
TOTAL Python coverage: 97.55%
generated_files_byte_identical_after_rebuild: true
GQ_CLEAN_ROOM_QUALIFIED
GQ_CLEAN_ROOM_IMAGE_READY
```

The clean-room browser tests include the real localhost origin, service-worker registration, cached offline shell and privacy/safety routes. This supersedes the earlier environment-policy skip from the original execution shell.

## Hosted application-protocol qualification

A temporary Railway vision fixture returned deterministic schema-valid observations. A separate temporary Railway runner acted as an external client through the public production HTTPS origin. It established:

- health 200 with live mode intentionally configured for the exercise;
- wrong access code → 401 in private mode;
- target analysis → schema-valid bounded observation + signed target ticket;
- product-label analysis → `unreviewed` and `recommendation_permission=false`;
- deterministic product match/start → eligible + signed encounter;
- before/after verification → clear + fixed 300 XP + signed completion receipt;
- repeat verification → identical receipt/idempotent result;
- root, manifest, service worker, privacy, safety and robots routes → 200.

The temporary provider and runner were deleted immediately afterward. Production was returned to AI-off-by-default. **This is network/application-protocol evidence, not evidence that a real model sees cleaning correctly.**

## Real-model qualification harness

`server/evaluation.py`, `scripts/evaluate_provider.py` and `eval/README.md` define a separate, privacy-preserving model gate. Reports contain case IDs and scored outcomes only—never image bytes, data URLs, OCR label text, prompts or credentials.

Default release minimums are 12 supported targets, 12 unsupported/hazard targets, 8 clear comparisons, 16 non-clear comparisons and 6 product-label pairs. A candidate must have:

- zero false-supported targets;
- zero required-hazard misses;
- zero false clears;
- zero provider-call failures;
- at least 80% supported-target surface+soil accuracy;
- at least 80% comparison-state accuracy;
- at least 80% product readability/name accuracy.

Those are minimum release gates, not a claim that the minimum dataset proves general safety.

## Exact-pair model-release qualification

An adversarial review found that the previous visual candidate classifier accepted the cartesian product of separately supported surfaces and dirt types, including **grease on ordinary glass** even though no enabled reviewed product matches that exact pair. The evaluator now derives allowed surface–soil pairs from the reviewed catalog, retaining the policy's explicit excluded materials and soils. A new regression covers the glass/grease counterexample and a 35-case matrix checks all surface–soil combinations against actual deterministic `match_product` eligibility.

This release-candidate code change was independently requalified in Railway with `Dockerfile.qualify` from Git commit `684c5e4fb2804a8eaee879b39149e882be47f838`: 405 Python tests, 34 Node tests, 97.55% coverage, and a byte-identical build. This narrows the visual evaluation candidate space; it does not certify any actual cleaning product or model.

## Catalog and mobile qualification

The deterministic catalog contains five exact consumer variants: two UK Method products plus three Finland-market Kiilto fragrance-free 600 ml products (Ikkuna, Koti and Keittiö). The supported material boundary remains ordinary uncoated glass and sound glazed ceramic only.

The policy suite exhaustively compares client/server outcomes across **1,680 combinations**. The expanded six-card loadout (five reviewed products plus the deliberate unreviewed-product safety card) is tested at 390 px and 320 px. A real 320 px overflow caused by long Finnish names was found and fixed.

Live-mode inventory is also reconciled before cleaning: removing an equipped product before the task starts invalidates that selection instead of allowing a stale loadout.

## Supply-chain evidence

The runtime/test dependency set is exact-pinned. Docker bases are digest-pinned. Railway clean installs run `pip check`; npm reported zero vulnerabilities.

A full OSV querybatch checked **32 exact package/version entries** spanning the Python runtime, Python test toolchain and TypeScript. The first expanded scan correctly caught a pytest 9.0.2 advisory; pytest was upgraded to 9.1.1 and the same scan then returned **0 known vulnerabilities / 0 errors**.

The old base scan identified four HIGH Python-tooling issues. The 2026-10-08 equivalent runtime rootfs scan passed after removing unused tooling, as detailed below. A separately inspectable scan of the final registry-published image remains a release-completeness improvement.

## OpenRouter ZDR and hard spending-cap gate

A dedicated fixed-model qualification path now requires a **read-only provider-side key check before any image upload or inference**. The OpenRouter key must have a non-resetting total spending cap of at most US$0.50, valid remaining headroom, BYOK usage counted toward the limit, and a non-management key type. A second read-only preflight checks the fixed model against OpenRouter's ZDR endpoint inventory and the request's required structured-output parameters. Every OpenRouter inference request then sets `provider.zdr=true`, `provider.data_collection="deny"`, and `provider.require_parameters=true`; strict Pydantic validation remains mandatory.

The current shared key has a cap above the authorized limit, so the gate correctly denies paid inference. No paid provider calls were made. A dedicated limited key is still required; see `docs/PAID_VISION_PRECHECK.md`.

Clean-room qualification on commit `74134ced3a32c8371466f9c4c50f18387e2fa97f` passed **412 Python + 34 Node tests = 446 total**, 97.76% combined coverage, and a byte-identical PWA build. The additional tests cover over-budget or resettable keys, unconfirmed BYOK caps, missing ZDR routes, and denial before model initialization or image upload.

## Remaining empirical/external gates

1. Qualify a real vision endpoint/model on the labeled private dataset.
2. Review/accept that provider's household-image privacy/retention terms and quota/cost behavior.
3. Test camera permission, capture, rotate/background/resume, Add to Home Screen and offline shell on the actual target phone(s).
4. Perform controlled real cleaning trials covering clear, partial, unchanged and unverifiable outcomes.
5. Complete an inspectable OS/base-image scan and an independent security review appropriate to the launch scope.
6. Complete actual screen-reader/mobile accessibility review.
7. Add the final service/operator privacy identity/contact before enabling a general public live-image service.
8. Make the repository public immediately before a submission that requires open source.

No practice fixture or mock-provider output should be described as real AI or physical-cleaning evidence.

## 2026-10-08 effective runtime security qualification

The original digest-pinned Python 3.13 slim base contained **four fixed HIGH findings** in bundled Python tooling (msgpack, setuptools and urllib3), while its Debian OS-package report had zero HIGH/CRITICAL issues. Refreshing the tag alone was insufficient: the registry still served the same pinned digest.

An isolated Railway Trivy **0.74.0** rootfs audit repeated the GrimeQuest runtime dependency install, ran `pip check`, uninstalled unused `msgpack`/`setuptools`/`urllib3`, removed pip itself after dependency installation, re-ran `pip check` and confirmed FastAPI/HTTPX/Pydantic/Pillow/Uvicorn imports. Its **whole-rootfs HIGH/CRITICAL scan passed** with `GQ_EFFECTIVE_RUNTIME_ROOTFS_TRIVY_PASS` (audit commit `66007e3c8ff6cd5e1a2d8f0475049c2bbfa8a511`). Only the Trivy executable itself was excluded: that scanner was injected solely into the disposable audit image and is not distributed in production.

The same package cleanup is now in the production `Dockerfile` (commit `b80ca1c26dfdaaf284903fe6f2a0023612f65fc3`). An isolated Railway canary deployment `765f8221-d02e-401b-8d20-56def7ca8f0a` built that exact Dockerfile and passed healthcheck. The application source itself did not change; previously qualified 439 automated test cases remain the software baseline. This confirms an **equivalent runtime filesystem**, not a cryptographically attested scan of the registry's final shipped image; preserve that distinction during final release review.

