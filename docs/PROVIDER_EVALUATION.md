# Vision provider evaluation — 2026-10-07

GrimeQuest needs **image input + strict structured text output**. The model is an observation component only; it never receives authority to grant chemical compatibility.

> **Real-API update (2026-10-08):** OpenRouter key authentication passed, but **no free route has qualified** for unattended household-photo analysis. Exact `qwen/qwen3.8-27b:free` returned HTTP 404 (free endpoint unavailable); `openrouter/free` returned one schema-shaped real image result in ~23.2 s but another request failed HTTP 404; fixed Gemma 4 31B with required ZDR routing returned HTTP 404. Do not configure public live-image access from this list. See [real provider smoke evidence](REAL_PROVIDER_SMOKE_20261008.md).

## Earlier candidates — unqualified for production

### 1. Qualification / zero-cost candidate: Qwen3.8 27B (free) through OpenRouter

Model: `qwen/qwen3.8-27b:free`

Why it is the first no-cost candidate:
- $0 model pricing;
- text + image + video input, text output;
- structured outputs supported;
- fixed model identity is more testable than a random free-model router;
- compatible with GrimeQuest's Chat Completions adapter.

Caveats:
- free endpoints are rate limited;
- when testing a free account that advertises 50 requests/day, set `GQ_MAX_CALLS_DAY` below that allowance (for example 45) so GrimeQuest fails closed before the provider quota;
- recent OpenRouter availability is materially below a paid production SLA;
- OpenRouter Free plan currently advertises 50 requests/day;
- privacy/data routing for a free multi-provider path must be reviewed before public live use;
- **no GrimeQuest accuracy claim exists until we test it on labeled cleaning images.**

### 2. Free fallback for prototyping: `openrouter/free`

This router is zero-cost, accepts image input and filters for features requested by the call, including structured output. It is useful for development continuity but chooses among free models, so its model identity and behavior vary. That makes it a poor primary choice for a safety-adjacent accuracy benchmark.

### 3. Low-cost fixed paid baseline: Google Gemini 3.8 Flash through OpenRouter

Model: `google/gemini-3.8-flash`

OpenRouter currently lists image input and structured output support. It is far more expensive than the free Qwen endpoint but has a fixed flagship-family model and strong provider uptime. Use it as an accuracy/reliability comparator, not automatically as the production winner.

## Required evaluation before enabling public live mode

Build a consented, labeled test set that includes:
- supported glazed ceramic with grease/light grime;
- supported ordinary uncoated glass with fingerprints/light grime;
- ambiguous materials that must become `unknown`;
- natural stone, wood, steel and glass-ceramic hob cases that must not be promoted into supported surfaces;
- heat/electrical/damage/mould/body-fluid/unknown-chemical hazard cases;
- before/after pairs: clear, partial, unchanged, wet/glare, obstructed, different target and changed framing;
- product-label pairs: readable, unreadable, truncated and adversarial text.

Measure **false-safe / false-clear errors separately** from ordinary classification accuracy. A model that looks better overall but creates more false clears should lose.

## Deployment rule

Do not set production `GQ_PROVIDER_*` variables until:
1. the exact model/endpoint passes the labeled set;
2. provider data terms are accepted for household photos;
3. rate/cost limits are understood;
4. a private `GQ_ACCESS_CODE` is generated;
5. a real phone flow is tested end to end.

Provider keys remain server-side only.
