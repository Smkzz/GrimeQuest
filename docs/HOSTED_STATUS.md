# Hosted status — 2026-10-06

## Repo-backed production service

The full GrimeQuest application is deployed on Railway:

- URL: `https://grimequest-web-production.up.railway.app/`
- Railway project: `grimequest`
- Environment: `production`
- Service: `grimequest-web`
- Production state: healthy / one Amsterdam replica
- Per-replica ceiling: 0.5 vCPU / 0.5 GB
- Builder: digest-pinned multi-stage Dockerfile
- Platform healthcheck: `/api/health`
- Live AI: disabled after mock-provider qualification
- Persistent workflow signing: configured
- Real-world cleaning validation: not performed

Railway builds the generated PWA assets inside the multi-stage Docker image, then serves the FastAPI backend and static PWA from one runtime container. The deployment uses Railway's injected `PORT`, bounded restart-on-failure behavior and the configured public app origin.

The first repo-backed deployment reached application startup but failed Railway's health gate because the strict Host allowlist rejected the platform's internal health-probe hostname. The boundary was changed narrowly so only `GET /api/health` is host-agnostic; all other routes keep the Host restriction. That change was requalified locally before redeployment:

- TypeScript/client tests: 34 passed;
- Python/API/browser tests: 235 passed;
- current automated qualification: 388 passed, one environment-policy skip;
- no failures or skips;
- deterministic PWA rebuild remained byte-identical.

The corrected deployment passed Railway's health gate. Later hardening refreshed runtime dependencies, added persistent workflow signing, stricter browser headers, privacy/safety offline pages, accessibility improvements, strict JSON-schema provider output and resource ceilings. Railway again completed a clean network install/build/start.

A temporary deterministic vision provider and external qualification runner then exercised the full public-HTTPS live workflow successfully (qualification runner deployment `52e34e89-4386-461e-9902-979dfa4a0b3e`). Both temporary services were deleted afterward.

## Current configuration

The deterministic catalog now contains five exact consumer variants: two UK Method products and three Finland-market Kiilto fragrance-free 600 ml sprays. The policy surface remains unchanged—ordinary uncoated glass and sound glazed ceramic only—and exhaustive client/server parity now covers 1,680 combinations.


Railway edge request tracing is enabled for status/latency visibility; Python auto-instrumentation remains disabled so this does not add application request-body/photo logging. Production is bounded to 0.5 vCPU and 0.5 GB RAM per replica.


The production service retains the app origin, model-attempt limit and persistent ticket-signing secret. Provider base/model/key and live access code were cleared after qualification, so the hosted app is again fail-closed in practice mode. `GQ_PUBLIC_LIVE` is explicitly disabled; the optional code-free public demo path is qualified but will not be enabled until a real provider has passed the accuracy/privacy gates.

The public Railway domain exists and the platform healthcheck succeeds. This execution environment could not independently resolve the Railway public hostname through its own DNS, so an external-browser fetch from this environment is not claimed. Railway's deployment state, replica state and healthcheck are the current hosting evidence.

## Remaining external gates

Before a real live-AI cleaning demo is qualified:

1. Make `Smkz-Entertainment/GrimeQuest` public if the hackathon requires open source. The repository is still private at this checkpoint.
2. Configure and qualify a vision-capable provider, server-side credential and private `GQ_ACCESS_CODE`; establish image/JSON protocol, cost controls, privacy terms, timeout/refusal behavior and provider-side spend limits.
3. Test PWA installation and camera permission/capture on an actual target phone/browser over the deployed HTTPS origin.
4. Perform controlled real-cleaning trials covering clear, partial, unchanged and unverifiable outcomes with supported products/surfaces.
5. Application-package advisories are currently clean in OSV (19 exact versions checked, 0 known vulnerabilities). Complete a trustworthy OS-package/final-container image scan before presenting this as a public production cleaning-advice service.

The deployed practice behavior must not be presented as real AI or physical-cleaning validation.
