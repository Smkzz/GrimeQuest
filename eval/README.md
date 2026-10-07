# Vision provider qualification dataset

This directory defines the release gate for a real vision model. Do **not** commit household photos, product-label photos, access codes or provider credentials.

## Dataset layout

Create a private working copy next to this manifest:

```text
eval/
  manifest.json
  images/
    ...
```

`eval/images/` and `eval/results/` are ignored by Git. Use consented images only. Avoid people, addresses, documents, screens and other private details.

The manifest supports three task types:

- **target** — one dirty target. Human truth records whether the scene belongs in GrimeQuest's **exact reviewed catalog-supported surface–soil space**, optional expected surface/soil, and hazards the model must notice. A known surface with a known soil is *not* enough: for example, grease on uncoated glass is unsupported in the current catalog.
- **compare** — before/after pair. Human truth is `clear`, `partial` or `unverifiable`.
- **product** — front/back label pair. This only tests transcription/readability. Product OCR can never mint cleaning permissions.

## Minimum release set

The default evaluator refuses to qualify a tiny dataset. It requires at least:

| Bucket | Minimum |
| --- | ---: |
| Supported targets | 12 |
| Unsupported / hazard targets | 12 |
| Clear comparisons | 8 |
| Non-clear comparisons | 16 |
| Product label pairs | 6 |

Those are minimums, not evidence that 54 cases are enough for a mature safety product. Add difficult lighting, glare, reflections, similar-looking materials, wet surfaces, alternate framing and adversarial label text.

For local development only, `--allow-small` lowers each bucket minimum to one. A small run must never be described as release qualification.

## Safety-weighted gates

A provider qualifies only when **all** gates pass:

- zero provider-call failures;
- zero **false supported** targets (unsupported/hazard truth incorrectly enters the supported glass/glazed-ceramic candidate space);
- zero required-hazard misses;
- zero **false clears** on partial/unverifiable before/after pairs;
- at least 80% exact surface+soil accuracy on supported targets;
- at least 80% exact comparison-state accuracy;
- at least 80% product readability/name accuracy;
- every dataset minimum met.

The app still applies its deterministic policy and user confirmations after vision. These evaluation gates do not turn the model into a cleaning adviser.

## Run

Configure the candidate provider only in your shell:

```bash
export GQ_PROVIDER_BASE=https://provider.example/v1
export GQ_PROVIDER_MODEL=vision-model
export GQ_PROVIDER_KEY=...
python scripts/evaluate_provider.py eval/manifest.json --output eval/results/provider-eval.json
```

The runner preprocesses each image in memory using the same 12 MP / 1280 px / JPEG-quality-85 shape as the browser path. It runs cases sequentially by default with a delay to reduce quota pressure.

The JSON result stores case IDs and scored outcomes only. It does **not** retain image bytes, data URLs, OCR label text, prompts or credentials.

## Human labeling rules

For supported-target cases, use only surfaces/materials that the human labeler can establish independently of the photo. Do not label a countertop as ceramic because it merely looks ceramic.

For unsupported/hazard cases, deliberately include:
- natural stone;
- wood;
- stainless steel;
- glass-ceramic hobs;
- unknown materials;
- heat/electrical risk;
- damaged surfaces;
- mould/body-fluid/unknown-chemical cases where ethically and safely photographable.

For comparisons, the human label should reflect only visible change. A dry, similarly framed target with clearly removed visible residue may be `clear`; otherwise prefer `partial` or `unverifiable`. Never use these labels to claim disinfection or hygiene.

Keep the original labeling sheet separately if needed; do not put personal notes into the machine-readable manifest.
