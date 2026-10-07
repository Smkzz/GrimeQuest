# Security model

## Intended deployment

A small, single-process PWA service with a public practice experience and fail-closed live mode, not an internet-scale multi-tenant account system. The hosted service uses HTTPS, exact-origin/Host checks, bounded resources and provider-call ceilings. Public-demo live access is opt-in and rate-limited. No security certification or independent penetration test has been performed.

## Implemented controls

- Server-only provider credentials; private per-tab application access code by default; exact origin and allowed-host checks; constant-time access comparison.
- Optional public demo mode can waive the shared code only by explicit server configuration. It remains same-origin, requires persistent signing, and refuses configuration above a bounded daily-attempt ceiling.
- JSON-only bounded POST bodies, explicit boolean consent (numeric `1` is rejected), strict schemas and no reflected validation payloads.
- Actual image decoding and content-type checks, pixel/byte/frame limits, metadata stripping, two concurrent decodes, no arbitrary file paths or client-supplied provider URL.
- Escaping of untrusted inventory/model text, a restrictive served-app CSP, no inline served-app scripts, no frame embedding and no third-party frontend scripts.
- Provider timeout/output limits, no redirects/retries or inherited proxy environment, bounded concurrency plus global hourly and daily provider-attempt ceilings.
- OpenRouter ZDR (`zdr=true`) and data-collection denial (`data_collection=deny`) are mandatory per-request, with endpoint parameter support required. Paid model evaluation refuses to upload images unless OpenRouter verifies a dedicated non-resetting total key limit ≤US$0.50 including BYOK usage.
- Railway edge tracing is enabled for operational status/latency, while FastAPI-native telemetry and Python auto-instrumentation are disabled to avoid duplicate exporters and application-level exception/log capture.
- HMAC-bound workflow and before-photo digest, purpose-specific tickets, one active comparison per encounter, idempotent cached completion and fixed rewards.
- No chemical permissions derived from label text or prompt content. Unknown inputs fail closed. The catalog has explicit expiry.
- Static-only service-worker allowlist; no private API/image caching; no app request-body logging.

OWASP's [file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) informed upload handling. This implementation uses bounded JSON data URLs rather than public file uploads or a filesystem upload folder.

## Residual risks / public-release gates

The model can still misobserve a scene or miss a hazard. Prompt instructions are not a complete prompt-injection defense; authority separation and schema restrictions limit the damage. User material/product confirmations can be wrong. A compromised same-origin script can read browser state and the tab access code; there is no assertion of tamper-proof local XP. Signed results are not authenticated photography or verified physical work.

Resource accounting is in process memory and per-IP limits may aggregate users behind a proxy. Multi-worker/multi-instance deployment would break the intended global limits and result idempotency. Workflow tickets now use a persistent server-side signing secret when configured, so legitimate signed encounters survive ordinary process restarts. Comparison-result deduplication and quotas remain process-local, so a restart can forget prior completion-cache state even though the signed workflow remains valid. A public multi-user release still needs durable account-level quotas, external spend limits, observability with private-field redaction and a reviewed privacy model.

Runtime dependencies were refreshed and pinned, project metadata was synchronized, Docker base images are digest-pinned, the container build runs `pip check`, and Railway completed a clean network install/build/start of that dependency set. The browser runtime has zero npm production dependencies. A full OSV querybatch audit checked 32 exact pinned entries across the Python runtime, Python test toolchain and TypeScript. It first caught a pytest 9.0.2 advisory; after upgrading to pytest 9.1.1 the same audit returned 0 known vulnerabilities / 0 errors. A reproducible Trivy 0.74.0 HIGH/CRITICAL rootfs scan of the **equivalent remediated runtime** now passes after unused pip/tooling removal; the production Dockerfile was separately built and health-checked in a canary. A direct scan of the final registry image and an independent penetration test have **not** been completed. Resolve those gates before treating the prototype as a generally available cleaning-advice service.

## Reporting

Do not send personal photos, product keys or full private labels in public issues. Once a repository owner publishes the project, that owner should configure a private vulnerability-reporting channel and policy. This source package does not invent a contact address.
