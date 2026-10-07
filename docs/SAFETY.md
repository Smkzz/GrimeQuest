# Safety design and catalog governance

## Non-negotiable boundaries

The application is a limited prototype, not a chemical safety authority. Vision is not allowed to recommend chemicals, mixtures, doses, contact times or temperatures. It emits a bounded observation schema. Product-label transcription is untrusted text and cannot update compatibility rules. Unsupported evidence returns `uncertain` or `blocked`, not a best guess.

The UI offers no mixing mechanic, speed reward, stronger-chemical reward or penalty for stopping. A comparison cannot establish hygiene or disinfection. A persistent warning discourages switching cleaners after an interrupted live task. Clearing that warning is an owner acknowledgement, not proof that a surface is residue-free.

The protocol follows the general principles of reading product directions, respecting surface instructions and not mixing products; see [CDC household cleaning guidance](https://www.cdc.gov/hygiene/about/when-and-how-to-clean-and-disinfect-your-home.html). For an actual exposure or emergency, stop interacting with this prototype and contact appropriate local poison/emergency services.

## What a conditional match means

A match requires an enabled, unexpired entry for the exact product variant, a supported confirmed surface and soil, no reported hazard, and all five explicit owner confirmations: exact bottle, label allows the target, target-care instructions allow it, no other cleaner is active, and the target is cool/safe.

This is still not a safety certification. Users can misidentify a surface or bottle; vision may miss hazards; a product label may differ by region or change. An acid/bleach compatibility database is intentionally absent. The prototype does not recommend drain cleaners, strong acids, bleach, oven cleaners, unknown decanted chemicals, solvents or treatments for mould/body fluids. These exclusions limit the application; they are not complete hazard detection.

## Included source-linked entries

The catalog is intentionally narrower than the general uses described by the manufacturers:

1. **Method glass + surface cleaner, mint, 828 ml, UK**. Enabled only for limited fingerprint/light-grime scenarios on confirmed ordinary uncoated glass or sound glazed ceramic, subject to both care labels. [Manufacturer product guidance](https://shop.methodproducts.co.uk/products/glass-surface-cleaner-mint/mglass.aspx?productid=mglass).
2. **Method daily kitchen cleaner, clementine, 828 ml, UK**. Enabled only for limited light grease/general-grime scenarios on confirmed sound glazed ceramic, not hobs, cookware, grout or a mixed-material assembly. [Manufacturer product guidance](https://shop.methodproducts.co.uk/products/daily-kitchen-cleaner-clementine/mkitchen.aspx?productid=mkitchen).
3. **Kiilto Ikkuna biohajoava puhdistussuihke Hajusteeton, 600 ml, Finland**. Manufacturer guidance covers glass, mirrors and other shiny surfaces; GrimeQuest enables only confirmed ordinary uncoated glass for fingerprints/light grime. [Manufacturer product guidance](https://kiiltokodinpuhdistus.fi/tuote/kiilto-ikkuna-biohajoava-puhdistussuihke-hajusteeton/).
4. **Kiilto Koti biohajoava yleispuhdistussuihke Hajusteeton, 600 ml, Finland**. Manufacturer guidance describes most wipe-clean household surfaces; GrimeQuest enables only confirmed sound glazed ceramic with light grime. [Manufacturer product guidance](https://kiiltokodinpuhdistus.fi/tuote/kiilto-koti-biohajoava-yleispuhdistussuihke-hajusteeton/).
5. **Kiilto Keittiö biohajoava puhdistussuihke Hajusteeton, 600 ml, Finland**. Manufacturer guidance covers grease/dirt on a broad set of kitchen surfaces; GrimeQuest enables only confirmed sound glazed ceramic for grease/light grime and explicitly does not inherit the broader sink/tap/hob examples. [Manufacturer product guidance](https://kiiltokodinpuhdistus.fi/tuote/kiilto-keittio-biohajoava-puhdistussuihke-hajusteeton/).

The review date records source inspection for this prototype, not review by a qualified chemical/materials professional. The catalog expires on 2027-01-04. Labels and manufacturer care guidance override the app. Similar names, colors, brands, barcode families or local-language variants must not be treated as equivalent.

## Adding a product responsibly

Before enabling an additional entry, record its exact market, name, size and variant; obtain legible current directions and warnings; check the intended object's care instructions; and define a deliberately narrow, source-supported material/soil set. Preserve sources and review dates. Treat absent compatibility evidence as absent, not as implied permission. Have the proposed real-use procedure reviewed by a suitably qualified person before public recommendation.

Add positive tests, explicit exclusions, uncertain material, changed label, unreadable label and expired-catalog tests. Update the catalog version and regenerate the client catalog. Run the exhaustive client/server parity test. Do not allow an AI-generated transcription, a successful-looking after photo, or previous user success to promote a rule automatically.

## Visual validation to perform before public live use

Collect consented, nonprivate before/after pairs for the exact supported tasks. Include unchanged images, angle changes, lighting changes, wet sheen, hidden dirt, covered targets, swaps, scratches mistaken for soil, subtle residue and unfamiliar materials. Use independent manual labels as a reference. Measure false clear and false safe-selection rates separately; report abstention and disagreement, not merely aggregate accuracy. No physical trial or such accuracy measurement has been completed for v0.1.0.
