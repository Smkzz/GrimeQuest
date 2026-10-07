# Real vision-provider smoke qualification — 2026-10-08

**Decision: NO-GO for public live-image analysis.** OpenRouter authentication succeeded and one real, licensed photograph received a valid model observation, but fixed free routing, repeatability, and Zero Data Retention (ZDR) requirements did not qualify. Production remains in practice mode; this is not a real cleaning-outcome study.

## Setup and trust boundaries

The operator entered `GQ_PROVIDER_KEY` directly in Railway. A temporary isolated Railway Function referenced that variable without printing, copying or storing its value. `GET https://openrouter.ai/api/v1/auth/key` returned HTTP **200**, authenticating the key. Temporary test infrastructure was subsequently deleted.

Only publicly licensed test photos were transmitted to the provider. No private household photo, product-label image or user data was transmitted.

The vision trials used GrimeQuest's target-observation structure: image input, `response_format.type=json_schema`, `strict=true`, `provider.require_parameters=true`, temperature 0, bounded output and a 25-second request deadline. Results below come from a temporary Bun-compatible protocol harness; they are not a complete Python production-provider evaluation with a labeled holdout.

## Observed real requests

| Request | Result | Meaning |
| --- | --- | --- |
| `qwen/qwen3.8-27b:free`, real glass fingerprints | **404** | OpenRouter said free access to that model was unavailable and proposed the paid slug `qwen/qwen3.8-27b`. No paid fallback was used. |
| `openrouter/free`, [real fingerprinted glass photograph](https://commons.wikimedia.org/wiki/File:Fingerprints_Dirty-Glass-Windows-House_IMG_5878_(8454776243).jpg) | **200**, ~23.2 s | Actual selected model: `dots-studio/dots-3-note-preview:free`. JSON observation shape validated. It saw fingerprints and visible soil but set material certainty/surface to unknown, conservatively avoiding a supported recommendation. This is a single sample, not a measured accuracy result. |
| `openrouter/free`, [real mixed dirty-dishes kitchen photograph](https://commons.wikimedia.org/wiki/File:Dirty_Dishes_(299743454).jpg) | **404**, ~6.7 s | OpenRouter reported no available endpoint capable of satisfying the requested parameters. No observation issued. |
| `google/gemma-4-31b-it:free` with `provider.zdr=true`, real glass photo | **404**, ~0.1 s | OpenRouter reported no endpoints available under the Zero Data Retention data policy. No observation issued. |

The photographs are credited to Emilian Robert Vicol (CC BY 2.0) and Mack Male (CC BY-SA 2.0), respectively. They were used for isolated inference only, not committed to this repository.

A contemporaneous catalog query found nine free image-capable model records, five with response-format-related support, and two free Gemma 4 candidates in the ZDR-filtered listing. An actual ZDR-required strict-schema call still failed. The catalog filter is not evidence of route availability for this API key.

## Safety, performance and privacy verdict

- **API credential:** valid.
- **A real multimodal call:** succeeded once and abstained conservatively.
- **Repeatable fixed-model delivery:** **not qualified**. The Qwen free endpoint returned 404; the free router chooses variable models and returned a parameter-routing error on another photograph.
- **Model deadline:** near its limit (23.2 s versus the current 25 s), without a latency distribution.
- **Schema:** one real free-router response passed a field/enum shape check; this is **not** a full 54+ case Pydantic evaluation.
- **Private image processing:** **not qualified**. An attempted ZDR-required free route had no eligible endpoint.
- **Physical cleaning:** no live provider observation has been compared against a ground-truthed real before/after household chore. No false-clear rate can be asserted.
- **Provider spending:** no paid model slug was invoked. Do not change to a billed endpoint without explicit owner authorization and a provider-side spend cap.

OpenRouter describes the `openrouter/free` route as selecting among free models. It also documents differences in inference-provider training and retention policies. Provider-native strict schema enforcement can vary; GrimeQuest must independently validate all structured observations.

## Next qualified step

1. Obtain explicit owner approval for a small **capped paid ZDR-capable fixed vision model**, or establish a genuinely available fixed zero-cost endpoint with acceptable privacy terms, image input and compatible structured output. Do **not** silently redirect from a free to a paid model.
2. Before enabling production, collect a private consented labeled holdout meeting `eval/README.md` minimums and run `scripts/evaluate_provider.py`, requiring **zero false-supported targets, zero required-hazard misses and zero false clears** alongside its other gates.
3. Complete actual target-phone capture/PWA installation/offline tests and a controlled real cleaning before/after session.
4. Keep `GQ_PROVIDER_BASE` and `GQ_PROVIDER_MODEL` unconfigured and `GQ_PUBLIC_LIVE=0` until those gates pass.

Temporary qualification services were deleted; no credential or real image bytes are stored in this report.
