# Hosted status — 2026-10-06

## Repo-backed production service

The full GrimeQuest application is deployed on Railway:

- URL: `https://grimequest-web-production.up.railway.app/`
- Railway project: `grimequest`
- Environment: `production`
- Service: `grimequest-web`
- Deployment: `5554ddd7-c9ff-4c35-aaeb-4cee4681cc43`
- Deployed source commit: `a7acac65c79db80e5e86516d2b196bd25503c21b`
- Region: Amsterdam / `europe-west4-drams3a`
- Replicas: 1
- Builder: Dockerfile
- Platform healthcheck: `/api/health`
- Deployment status at qualification: SUCCESS
- Live AI: disabled
- Real-world cleaning validation: not performed

Railway builds the generated PWA assets inside the multi-stage Docker image, then serves the FastAPI backend and static PWA from one runtime container. The deployment uses Railway's injected `PORT`, bounded restart-on-failure behavior and the configured public app origin.

The first repo-backed deployment reached application startup but failed Railway's health gate because the strict Host allowlist rejected the platform's internal health-probe hostname. The boundary was changed narrowly so only `GET /api/health` is host-agnostic; all other routes keep the Host restriction. That change was requalified locally before redeployment:

- TypeScript/client tests: 34 passed;
- Python/API/browser tests: 235 passed;
- total automated tests: 269 passed;
- no failures or skips;
- deterministic PWA rebuild remained byte-identical.

The corrected deployment passed Railway's health gate. The temporary `grimequest-practice` Railway Function used during bring-up was removed after the full service became healthy.

## Current configuration

The service currently has `GQ_APP_ORIGIN` and `GQ_MAX_CALLS_HOUR` configured. Provider configuration and the private live-mode access code are intentionally absent, so `live_ready` remains false and the default hosted experience is practice mode.

The public Railway domain exists and the platform healthcheck succeeds. This execution environment could not independently resolve the Railway public hostname through its own DNS, so an external-browser fetch from this environment is not claimed. Railway's deployment state, replica state and healthcheck are the current hosting evidence.

## Remaining external gates

Before a real live-AI cleaning demo is qualified:

1. Make `Smkz-Entertainment/GrimeQuest` public if the hackathon requires open source. The repository is still private at this checkpoint.
2. Configure and qualify a vision-capable provider, server-side credential and private `GQ_ACCESS_CODE`; establish image/JSON protocol, cost controls, privacy terms, timeout/refusal behavior and provider-side spend limits.
3. Test PWA installation and camera permission/capture on an actual target phone/browser over the deployed HTTPS origin.
4. Perform controlled real-cleaning trials covering clear, partial, unchanged and unverifiable outcomes with supported products/surfaces.
5. Run a current dependency/container vulnerability review before presenting this as a public production cleaning-advice service.

The deployed practice behavior must not be presented as real AI or physical-cleaning validation.
