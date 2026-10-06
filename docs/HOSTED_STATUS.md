# Hosted status — 2026-10-06

## Practice PWA

A practice-only GrimeQuest build is deployed on Railway:

- URL: `https://grimequest-practice-production.up.railway.app/`
- Railway project: `grimequest`
- Environment: `production`
- Service: `grimequest-practice`
- Deployment: `0910514c-8111-4efe-ad15-1e2ca2789bc5`
- Region: Amsterdam / `europe-west4-drams3a`
- Replicas: 1
- Platform healthcheck: `/api/health`
- Health status at qualification: SUCCESS
- Live AI: disabled
- Real-world cleaning validation: not performed

The hosted practice build includes a web-app manifest, service worker and offline shell routes. This checkpoint confirms Railway can host the illustrative walkthrough over HTTPS and that Railway's HTTP healthcheck reaches the process. It does **not** establish physical-device installability, phone camera behavior, real product matching, vision-model accuracy, or cleaning-result accuracy.

## Intended repo-backed service

The `grimequest-web` Railway service exists but is offline. Its reserved HTTPS origin is `https://grimequest-web-production.up.railway.app/`. Railway's GitHub installation currently cannot read the private `Smkz-Entertainment/GrimeQuest` repository, so the Dockerfile has not been built by Railway.

The pending service is already configured for Amsterdam, `/api/health`, bounded restart-on-failure behavior, Dockerfile path `Dockerfile`, `GQ_APP_ORIGIN=https://grimequest-web-production.up.railway.app`, and `GQ_MAX_CALLS_HOUR=40`. Provider credentials and the private app access code are intentionally unset.

The repository now contains:

- a multi-stage Dockerfile that builds generated PWA assets before the Python runtime stage;
- runtime support for Railway's injected `PORT`;
- `railway.json` with the Dockerfile builder, `/api/health` healthcheck, bounded restart policy, and Amsterdam region.

The exact patched source was requalified locally after these deployment changes:

- TypeScript/client tests: 34 passed;
- Python/API/browser tests: 235 passed;
- total: 269 passed;
- no failures or skips.

An actual Docker build was not run in the qualification environment because a Docker daemon was unavailable.

## External blockers

Before the full live application can be qualified:

1. Grant Railway's GitHub installation access to `Smkz-Entertainment/GrimeQuest`, or make the repository public.
2. For the hackathon submission, make the repository public because the rules require open source.
3. Configure a tested vision provider and server-side credentials. Do not expose the provider key to the browser.
4. Set `GQ_APP_ORIGIN` to the final HTTPS app origin and generate a private `GQ_ACCESS_CODE`.
5. Run the repo-backed Docker deployment and verify the exact deployed source/configuration.
6. Test PWA installation and camera permission/capture on a real phone.
7. Perform controlled real-cleaning trials, including clear, partial, unchanged and unverifiable outcomes.

The current public practice URL should not be presented as a qualified cleaning-advice product.
