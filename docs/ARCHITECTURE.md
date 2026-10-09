> **Historical architecture note:** The workflow below describes the earlier
> optional AI/product-matching prototype retained as guarded source code.
> As of October 9, the **public player experience** starts in
> **client/casual.ts** and uses the on-device before photo → clean → after
> photo → self-reported XP/monster-collection loop. It makes no runtime AI
> request and never selects a material, product or chemical method. See
> [README](../README.md) and [current release audit](MONSTER_RELEASE_AUDIT_20261009.md).
> Treat the following API design and limits as background on dormant source,
> not the live player journey.

# Architecture

## Deliberate small-system choices

A strict TypeScript client compiles to one JavaScript file. A Python FastAPI server serves the static PWA and a same-origin API. The source application has no bundler, runtime npm dependencies, database, account service, analytics, SDK credential exposure or mandatory paid integration. This keeps the install surface small enough for a solo prototype. A larger team could migrate view rendering to a component framework without changing the domain or API contracts.

The TypeScript `GQ` namespace is an explicit small-app packaging tradeoff, not a global-state pattern to extend indefinitely. Domain functions, persistence, camera lifecycle and view/controller code are in separate source files. Rendering escapes untrusted text; URLs from product evidence are fixed catalog entries. The server supplies a restrictive CSP when serving the full app. The standalone preview necessarily inlines scripts/styles and is a separate practice-only delivery form.

## Main flows

```text
Before photo -> resize / metadata removal -> explicit upload consent
 -> bounded server normalization -> vision observation (no cleaning advice)
 -> signed target receipt -> owner confirms material and soil
 -> exact owned catalog product -> deterministic label/surface/hazard policy
 -> five explicit owner confirmations -> signed encounter receipt
 -> actual cleaning outside the application
 -> dry after photo + original before photo + explicit comparison consent
 -> digest binding / identical-image guard / duplicate suppression
 -> model comparison -> deterministic adjudication -> signed result receipt
 -> fixed reward -> mode-isolated local journal
```

Product labels have a separate path:

```text
Front + instructions photo -> bounded transcription -> UNREVIEWED inventory note
```

There is **no** edge from transcription to compatibility permission. A model cannot rewrite the catalog or generate usage procedures. User material confirmation is an attestation, not sensor evidence. Manufacturer directions and object-care guidance remain the practical authority.

## API

| Route | Purpose |
| --- | --- |
| GET `/api/health` | Readiness and nonsecret configuration metadata |
| GET `/api/catalog` | Public, versioned reference catalog |
| POST `/api/analyze-target` | Structured observation and signed before-photo binding |
| POST `/api/analyze-product` | Front/back label transcription, always unreviewed |
| POST `/api/match` | Deterministic conditional policy result |
| POST `/api/start` | Check signed observation and all confirmations before minting an encounter |
| POST `/api/verify` | Check original photo, adjudicate comparison, issue bounded result |

All POST routes require a configured live adapter, exact same-origin request, JSON content type and a private server access code. OpenAPI is available at `/api/openapi.json`; Swagger/ReDoc are disabled. Health readiness only means configuration is present, not that a real provider or cleaning procedure has been qualified.

## Limits

Input bodies are streamed into at most 5.7 MB of memory with a 12-second upload deadline. Each decoded input is at most 2 MB and 12 megapixels; animated images, SVG, HEIC, malformed encodings and content/MIME mismatches are rejected. Two pixel decodes can run simultaneously. Re-encoding creates a new metadata-free RGB buffer and a maximum 1600-pixel edge. The browser normally resizes to 1280 pixels first.

The provider adapter permits two concurrent model calls, defaults to 40 attempts per server-hour and 20 per client IP-hour. Failed attempts still count. Requests have an overall 25-second provider deadline, no automatic retries/redirects and a 100 KB response limit. The browser timeout is 35 seconds. These are resource bounds, not a fixed monetary budget or a complete distributed abuse defense.

Receipts are HMAC-SHA256 signed using an ephemeral random server secret. Target/encounter receipts last two hours; completion receipts last 24 hours. The completion cache is bounded, holds only result metadata, and blocks concurrent verification for one encounter. Repeated clears return an existing result rather than triggering more model calls. A restart invalidates old receipts. There is no durable cross-instance replay ledger; **one process** is required.

## Offline and local data

The service worker precaches a fixed allowlist of app-shell assets and practice illustrations. It does not intercept API requests, cross-origin requests, query-bearing requests, photos or arbitrary files. It does not call `skipWaiting`, so a new worker is not deliberately forced into an active quest.

Inventory and the latest 200 comparison records are local; up to 40 products are accepted. Displayed XP is derived from that retained history, not a lifetime account balance. Corrupt stored data is preserved until an explicit reset rather than silently overwritten. The access code uses session storage. Photos live only in memory for the current workflow; they are not a persistent album.

Physical camera access and service-worker installation require real browser/platform qualification. Unit tests cover the worker's cache policy, and Chromium tests exercise UI behavior with declared test adapters. Neither constitutes physical-device validation.

## Supported output semantics

Only `same_target && comparable && visible_soil_before && !wet_or_glare && !obstructed`, plus `residue_after=not_visible` and `improvement=substantial`, can produce a clear. Any ambiguous observation returns zero XP. Other nonambiguous outcomes are partial, also zero XP. This conservative mapping is deterministic; whether a model's observations are correct remains an empirical question.

A receipt establishes that this software processed particular image digests and observations. It does not establish chemical safety, sanitation, image authenticity, authorship of the physical action or resistance to a user editing local storage.
