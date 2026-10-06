# Build plan and completed iterations

Status: local implementation complete; empirical live/public qualification outstanding.

| Stage | Outcome |
| --- | --- |
| Freeze scope | One-target quest; real inventory; explicit practice/live separation; no fake cleanliness percentages or chemical-mixing mechanics |
| Design trust boundaries | Model observation separated from a versioned deterministic product policy; unknown products remain unreviewed |
| Build server vertical slice | Strict FastAPI/Pydantic API, image normalization, signed target/encounter/results, bounded provider adapter |
| Build mobile interface | Quest selection, original illustrated mascot/scenes, material confirmation, product cards, care checks, photo comparison, journal and settings |
| Add persistence/recovery | Bounded local store, tab-only access code, interrupted-task warning and corruption preservation |
| Add PWA delivery | Static manifest/icons, explicit app-shell cache, standalone single-file practice preview |
| First tests | Backend matrix, strict schema, provider-failure, upload, receipt and rate-bound tests passed |
| Adversarial fixes | Rejected numeric consent; strengthened missing-attestation checks; guarded non-ASCII headers; bounded decode concurrency |
| UI/recovery fixes | Cancelled stale file decodes; kept mode switching from losing an active live task; showed unsupported product state; improved small-screen input sizing |
| Regression tests | Practice/live browser flows, export, label scan, XSS text handling, duplicates, concurrent comparison and client/server rule parity |
| Handoff | Source, prebuilt preview, test logs, screenshots, usage instructions, manual CI recipe and release gates |

The browser environment blocks all URL navigation and physical capture by policy. Tests therefore injected the generated app in a browser document and used declared storage/API adapters. No browser policy was disabled. API enforcement was separately tested at HTTP/ASGI boundaries. Installation, TLS and a real phone remain explicitly unverified.

No existing project repository or code was imported. No paid model calls, public deployment, database writes, repository push, cloud CI run or third-party account changes were performed.
