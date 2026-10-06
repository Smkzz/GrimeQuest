# Security model

## Intended deployment

A small, single-process **private preview**, not an internet-scale public multi-tenant service. Keep the default loopback binding until HTTPS, origin configuration, access control, provider privacy and budget controls are reviewed. The private application code is not a user-account system and cannot replace production authentication. No security certification or independent penetration test has been performed.

## Implemented controls

- Server-only provider credentials; private per-tab application access code; exact origin and allowed-host checks; constant-time access comparison.
- JSON-only bounded POST bodies, explicit boolean consent (numeric `1` is rejected), strict schemas and no reflected validation payloads.
- Actual image decoding and content-type checks, pixel/byte/frame limits, metadata stripping, two concurrent decodes, no arbitrary file paths or client-supplied provider URL.
- Escaping of untrusted inventory/model text, a restrictive served-app CSP, no inline served-app scripts, no frame embedding and no third-party frontend scripts.
- Provider timeout/output limits, no redirects/retries or inherited proxy environment, bounded concurrent and hourly model calls.
- HMAC-bound workflow and before-photo digest, purpose-specific tickets, one active comparison per encounter, idempotent cached completion and fixed rewards.
- No chemical permissions derived from label text or prompt content. Unknown inputs fail closed. The catalog has explicit expiry.
- Static-only service-worker allowlist; no private API/image caching; no app request-body logging.

OWASP's [file-upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) informed upload handling. This implementation uses bounded JSON data URLs rather than public file uploads or a filesystem upload folder.

## Residual risks / public-release gates

The model can still misobserve a scene or miss a hazard. Prompt instructions are not a complete prompt-injection defense; authority separation and schema restrictions limit the damage. User material/product confirmations can be wrong. A compromised same-origin script can read browser state and the tab access code; there is no assertion of tamper-proof local XP. Signed results are not authenticated photography or verified physical work.

Resource accounting is in process memory and per-IP limits may aggregate users behind a proxy. Multi-worker/multi-instance deployment would break the intended global limits and result idempotency. A server restart invalidates receipts. Production needs durable account-level quotas, external spend limits, observability with private-field redaction and a reviewed privacy model.

Dependency versions were pinned to the tested environment. A fresh dependency-advisory scan, container image scan and clean network install were **not** completed. The optional container recipe is unbuilt here and its base image tag is not digest-pinned. Resolve those gates before exposure rather than treating a test pass as a security guarantee.

## Reporting

Do not send personal photos, product keys or full private labels in public issues. Once a repository owner publishes the project, that owner should configure a private vulnerability-reporting channel and policy. This source package does not invent a contact address.
