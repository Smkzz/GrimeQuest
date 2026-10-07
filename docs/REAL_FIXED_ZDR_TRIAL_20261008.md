# Fixed-model, ZDR-required real-image exploratory trial — 2026-10-08

**Decision:** The fixed Google Gemini 2.5 Flash Lite route **passed three exploratory, live multimodal protocol calls**. This is **not** a complete model release qualification, and GrimeQuest live AI remains disabled on the public deployment.

## Authorization and cost controls

The owner first authorized no more than €1 total, conditioned on strict ZDR and a provider-side hard spending cap. The owner subsequently authorized bypassing the earlier €0.50 key-specific threshold **for this limited exploratory qualification using the existing key**. The existing OpenRouter key was confirmed through read-only `GET /api/v1/key`: non-resetting total limit **US$10**, about **US$6.27 remaining**. That provider-side limit is *not* a €1 cap.

A disposable test function enforced three requests maximum, no retries, `max_tokens=900`, a 30-second per-call timeout, and a **US$0.25 account-usage-delta stop** checked before each call. This software-side stop does **not** replace a dedicated provider-enforced €1 cap for broad evaluation. The key was referenced inside Railway; no key text was printed, downloaded or committed.

The immediate OpenRouter key-account usage readings at the beginning and end of the 3-call run both reported `US$3.73433101` (observed delta 0); billing can be delayed or influenced by other callers, so this does **not** establish that the requests were free.

## Provider qualification

The read-only `GET /api/v1/endpoints/zdr` endpoint returned **two active endpoints** for the fixed model `google/gemini-2.5-flash-lite` with `structured_outputs`, `response_format`, `temperature`, and `max_tokens` advertised. Every test inference then required:

```json
{
  "provider": {
    "require_parameters": true,
    "zdr": true,
    "data_collection": "deny"
  }
}
```

All requests used image input plus strict JSON-schema response formatting. No provider automatically substituted another model.

| Case | Live status / latency | Observation | Preliminary safety outcome |
| --- | --- | --- | --- |
| [Fingerprints on glass (CC BY 2.0)](https://commons.wikimedia.org/wiki/File:Fingerprints_Dirty-Glass-Windows-House_IMG_5878_(8454776243).jpg) | **200 / 2009 ms** | Object: handprint on glass; dirt: fingerprints; surface: unknown, material tentative; hazards: none | Conservative abstention; no unsupported product recommendation |
| [Mixed dirty dishes / sink (CC BY-SA 2.0)](https://commons.wikimedia.org/wiki/File:Dirty_Dishes_(299743454).jpg) | **200 / 1336 ms** | Object: dirty dishes in sink; surface: stainless steel; dirt: light grime; hazards: none | Excluded by the current glass/glazed-ceramic catalog |
| Deliberately mismatched pair using those two independent photos | **200 / 1413 ms** | `same_target=false`, `comparable=false`, `improvement=uncertain` | Unverifiable; no false clear or XP |

All three responses were successfully decoded and passed the temporary qualification harness's strict field/enum/range checks. `finish_reason=stop` and the returned model slug matched the chosen fixed model in all three. This harness was written as an isolated Bun test, **not** the full Python Pydantic evaluation used for release. Results were limited to non-private, public-source photographs. The temporary function was deleted after recording the result.

## What this qualifies and what it does not

**Positive evidence:** fixed-model accessibility under ZDR-required OpenRouter routing, parameter-compatible structured output, low observed latency on these three photos, sensible initial abstention and a correct non-comparable result.

**Not qualified:** statistically meaningful model accuracy, 12+ independently verified supported images, 12+ unsupported/hazard images, 8 actual clear before/after cleaning examples, 16 nonclear examples, 6 genuine product-label pairs, real-user photo processing terms, adversarial misclassification rate, actual disinfection, physical cleaning success, provider availability under sustained load or phone-camera behavior.

The existing `scripts/evaluate_provider.py` still demands a dedicated non-resetting `<=US$0.50` provider key before the **full** 54+ case evaluation. That policy was **not** disabled in production source for this exploratory experiment. Before running the full benchmark on the shared key, the explicit waiver should be implemented as a narrowly scoped, auditable non-production evaluation mode, with a persistent task-level spend ledger and an overall €1 stop—or use a dedicated key.

**Public live AI remains disabled.** Do not promote three successful smoke calls into a public-use safety certification.
