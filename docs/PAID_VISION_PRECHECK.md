# Bounded paid vision qualification — operator runbook

**State (2026-10-08): blocked pending a dedicated OpenRouter key. No paid inference has been made.**

The owner authorized at most **€1 total** for fixed-model real-vision qualification, **only if** both provider-enforced spending limits and Zero Data Retention (ZDR) routing are verified before any paid request.

## Hard cost gate — independent of GrimeQuest process counters

The existing OpenRouter key was authenticated with the read-only `GET /api/v1/key` endpoint. Its current total USD limit was **larger than the authorized evaluation budget**, so it was rejected. Changing the shared key could disrupt other projects; do **not** edit that key.

Create a dedicated **GrimeQuest test key** in [OpenRouter API Keys](https://openrouter.ai/settings/keys) with:

- Name: `GrimeQuest-qualification`
- **Total spending limit: US$0.50** (a conservative cap below the €1 authorization)
- **Reset: none / never**, not daily, weekly, or monthly
- **Include BYOK spending in the limit: enabled**
- No additional payment sources, fallback keys or unrelated consumers

Replace `GQ_PROVIDER_KEY` in Railway's `grimequest-web → Variables` with the dedicated key **only after that cap is saved in OpenRouter**. Do not commit or paste the secret. Other production provider settings must remain disabled until qualification passes.

The evaluator now refuses to run a single image request unless the *provider itself* returns all of these values from `GET https://openrouter.ai/api/v1/key`:

- `0 < limit <= 0.50` USD
- `0 <= limit_remaining <= limit`
- `limit_reset is null`
- `include_byok_in_limit is true`
- `is_management_key is false`

An absent, resettable, inconsistent or oversized limit returns a failure **before constructing the vision client or uploading any image**. A missing compatible ZDR endpoint also fails before inference. Preflight eligibility does not guarantee that the live endpoint will stay available. This is stronger than `GQ_MAX_CALLS_DAY`, which is only a per-process call-count budget.

## Data and provider routing gate

Every request made by GrimeQuest's OpenRouter adapter now contains:

```json
{
  "provider": {
    "require_parameters": true,
    "zdr": true,
    "data_collection": "deny"
  }
}
```

No fallback may loosen these constraints. Strict JSON-schema output is also requested and independently validated with Pydantic. A provider routing error or malformed response fails closed.

The initial fixed paid candidate is `google/gemini-2.5-flash-lite`, which is listed with image input, structured JSON and ZDR-capable endpoints. **The exact combination has not yet passed a paid inference call.** Model metadata does not prove request-level endpoint availability.

The reference documentation is:
- [OpenRouter API key limits](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-key)
- [Creating limited API keys](https://openrouter.ai/docs/api/api-reference/api-keys/create-keys)
- [ZDR provider routing](https://openrouter.ai/docs/guides/get-started/sovereign-ai)
- [Structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs)

## Qualification steps once a dedicated key exists

1. Re-run the read-only `/api/v1/key` check. Stop if any spending guard is missing.
2. Query `GET /api/v1/endpoints/zdr` **without sending an image**. The fixed model must have an advertised ZDR endpoint supporting JSON response formatting, temperature and output limits; the evaluation runner now enforces this preflight too.
3. Send one licensed, non-private image using the fixed model and request-level ZDR. Verify HTTP 200, schema compliance, actual model identity, no unknown fallback, and response latency.
4. Re-check the remaining *provider-side* key limit. Stop if any unexpected charge or routing change appears.
5. Run the private, consented `eval/README.md` holdout set through `scripts/evaluate_provider.py`, with the new spending guard. The runner stops immediately on provider failure or a safety-critical false-supported/false-clear/hazard miss.
6. Apply the mandatory accuracy and abstention gates. Do not infer safety from a handful of photographs. Never commit images, addresses or readable labels.
7. Complete target-phone, camera, safety and actual cleaning trials.
8. Only after qualification and owner approval configure production `GQ_PROVIDER_BASE`, `GQ_PROVIDER_MODEL`, a private access code, and subsequently consider public demo mode.

**No paid request is authorized when the existing larger-limit key is the only available credential.**
