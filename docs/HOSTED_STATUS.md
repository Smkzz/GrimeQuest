# Hosted status — 2026-10-07

## Production service

The repo-backed GrimeQuest application is deployed on Railway:

- URL: `https://grimequest-web-production.up.railway.app/`
- Railway project: `grimequest`
- Environment: `production`
- Service: `grimequest-web`
- Region: Amsterdam / `europe-west4-drams3a`
- Replicas: 1
- Per-replica ceiling: 0.5 vCPU / 0.5 GB
- Builder: digest-pinned multi-stage `Dockerfile`
- Platform healthcheck: `/api/health`
- Railway edge tracing: enabled
- Python auto-instrumentation: disabled
- FastAPI native traces/metrics/log export: disabled
- Persistent workflow signing: configured
- Live AI: intentionally disabled
- Public-demo access: intentionally disabled
- Real-world cleaning validation: not performed

The application builds generated PWA assets inside the image, serves the FastAPI API and PWA from one runtime container, honors Railway's injected `PORT`, and runs as a non-root application user. Provider/model/key and live access code are unset in the production service, so live analysis fails closed while practice mode remains available.

## Automated qualification state

The current software release candidate has passed a separate Railway clean-room build on the same Python 3.13 runtime family as production:

- Python: 3.13.16
- Node: 22.23.3
- Python/API/browser/evaluation tests: 413 passed
- client/Node tests: 36 passed
- total: **449 / 449 passed**
- skips/warnings: **0**
- Python combined coverage: **97.76%**
- client/server policy parity: **1,680 combinations**
- real-origin Chromium PWA/service-worker/offline test: pass
- generated rebuild: byte-identical
- npm clean-install audit: 0 vulnerabilities
- full OSV exact-version audit: 32 checked, 0 vulnerable, 0 errors

The clean-room image emits `GQ_CLEAN_ROOM_QUALIFIED` only after strict TypeScript, client tests, Python tests/coverage and build reproducibility all pass.

## Hosted protocol evidence

A previous temporary deterministic vision provider plus an external Railway runner exercised the complete live protocol through the public HTTPS origin: private-access rejection, bounded target observation, product scan staying unreviewed, deterministic match/start, signed encounter, visual comparison, fixed XP, signed completion and idempotent repeat. All temporary qualification services were removed afterward.

That evidence qualifies the network/application protocol. It **does not** qualify a real model's visual accuracy or a physical cleaning outcome.

## Access / cost posture

Production remains deliberately conservative:

- `GQ_PUBLIC_LIVE=0`
- `GQ_MAX_CALLS_HOUR=40`
- `GQ_MAX_CALLS_DAY=200`
- no configured provider key/model
- one application replica
- no database, persistent photo store, analytics SDK or advertising SDK

An opt-in code-free public-demo access path exists for judging, but must stay off until the exact real vision provider passes the labeled evaluation/privacy gates. For a free provider with a lower quota, the application daily ceiling must be set below the provider allowance.

## 2026-10-08 effective runtime security qualification

The original digest-pinned Python 3.13 slim base contained **four fixed HIGH findings** in bundled Python tooling (msgpack, setuptools and urllib3), while its Debian OS-package report had zero HIGH/CRITICAL issues. Refreshing the tag alone was insufficient: the registry still served the same pinned digest.

An isolated Railway Trivy **0.74.0** rootfs audit repeated the GrimeQuest runtime dependency install, ran `pip check`, uninstalled unused `msgpack`/`setuptools`/`urllib3`, removed pip itself after dependency installation, re-ran `pip check` and confirmed FastAPI/HTTPX/Pydantic/Pillow/Uvicorn imports. Its **whole-rootfs HIGH/CRITICAL scan passed** with `GQ_EFFECTIVE_RUNTIME_ROOTFS_TRIVY_PASS` (audit commit `66007e3c8ff6cd5e1a2d8f0475049c2bbfa8a511`). Only the Trivy executable itself was excluded: that scanner was injected solely into the disposable audit image and is not distributed in production.

The same package cleanup is now in the production `Dockerfile` (commit `b80ca1c26dfdaaf284903fe6f2a0023612f65fc3`). An isolated Railway canary deployment `765f8221-d02e-401b-8d20-56def7ca8f0a` built that exact Dockerfile and passed healthcheck. The application source itself did not change; previously qualified 439 automated test cases remain the software baseline. This confirms an **equivalent runtime filesystem**, not a cryptographically attested scan of the registry's final shipped image; preserve that distinction during final release review.

## Remaining external gates

1. Qualify the exact real vision model/endpoint with the private labeled dataset.
2. Accept/document provider privacy, retention, quota and cost terms for household images.
3. Run actual target-phone camera/PWA install/offline tests.
4. Perform controlled real cleaning trials.
5. Remediated runtime-equivalent rootfs now passes Trivy HIGH/CRITICAL inspection; still complete an independent security review and preferably a direct final published-image scan.
6. Complete actual screen-reader/mobile accessibility review.
7. Add the final service/operator privacy identity/contact before a general public live-image launch.
8. Make the GitHub repository public only at the final submission/publication step.

Practice, deterministic fixture and mock-provider results must never be presented as real AI or physical-cleaning evidence.
