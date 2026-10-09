> **Current game (October 9):** Original monster SVG art, local images,
> self-reported progress and text-only sharing use no runtime AI service.
> The ZXing scanner, cloud vision and product-discovery references below
> describe guarded historical components still present in the source or
> production build; they are not visible in the current casual game.
> Their license notices are preserved for compliance.

# Third-party notices

Original application code and fixture illustrations use the MIT license in LICENSE. Product names identify real catalog variants; no affiliation or endorsement is implied. Product reference descriptions are narrow paraphrases with links to manufacturer guidance. Do not assume trademark rights or a right to redistribute full product labels.

Runtime dependencies include FastAPI (MIT), Starlette (BSD-3-Clause), Uvicorn (BSD-3-Clause), Pydantic (MIT), HTTPX (BSD-3-Clause) and Pillow (HPND). Development dependencies include TypeScript (Apache-2.0), pytest (MIT), pytest-cov (MIT) and Playwright (Apache-2.0). Their transitive dependencies retain their own notices and licenses. Dependencies are installed separately, not bundled in the source ZIP. Review current package license files before redistributing binaries.

System fonts are referenced by CSS; no font files are distributed. SVG/PNG practice scenes and the mascot/icon geometry are original, not photographs of a real cleaning result.

Official implementation references are linked inline in README, SECURITY and SAFETY. The TypeScript 5.8.3 package integrity was read from the official npm package metadata. Manual CI action pins were verified against the corresponding official action release commits on 2026-10-06; being pinned does not certify that a dependency is vulnerability-free.

The self-hosted desktop QR code encoder includes **qr-creator** (Copyright © 2017 The Nimiq Foundation, MIT), derived from jquery-qrcode (Lars Jung, MIT) and the JavaScript QR Code Generator (Kazuhiko Arase, MIT). The vendored browser source has its ES-module export removed to run under the existing self-hosted, no-inline-script CSP. Its original license is preserved in `web/vendor/qr-creator.LICENSE.txt`. There is no third-party QR or tracking endpoint.

Product-label OCR uses **Google Cloud Vision API** under Google's applicable service and data-processing terms, only when operator-enabled and separately approved by the player. This is an externally operated commercial service, not vendored open-source code. Each consented front/back batch requests TEXT_DETECTION and DOCUMENT_TEXT_DETECTION once (two billable image units). OCR outputs remain unverified and cannot create chemical-use permissions. The old Tesseract/Leptonica OCR binaries and traineddata are no longer installed or used.

The barcode camera uses **ZXing for JavaScript**, `@zxing/library` v0.21.3, licensed MIT. Its browser UMD distribution and license are copied at image-build time from the exact-version published npm archive and self-hosted as `web/vendor/zxing-0.21.3.min.js` and `web/vendor/zxing.LICENSE.txt`. Browser barcode decoding runs locally; neither photos nor video frames are uploaded. GrimeQuest does not load scanner code from third-party CDNs on player devices.

Worldwide community barcode and deliberate name searches use the Open Facts family: **Open Products Facts, Open Beauty Facts, Open Food Facts and Open Pet Food Facts**. These community indexes use the Open Database License (ODbL), including attribution and share-alike conditions. GrimeQuest requests only GTIN, brand, product name and quantity; each candidate links to its exact source. Suggestions are displayed transiently and only user-confirmed individual records are saved in browser inventory. No external database is merged into the independent reviewed chemical-safety policy/catalog. See https://openfoodfacts.github.io/documentation/docs/Product-Opener/api/ and https://opendatacommons.org/licenses/odbl/ .


## Additional barcode identity sources (optional, unreviewed)

When the four Open Facts indexes have no record, server-side lookups may request a **numeric GTIN only** from [UPCitemdb](https://www.upcitemdb.com/api/) and [EAN-Suche](https://ean-suche.net/api-doku). They return unverified identity suggestions, never safety instructions. UPCitemdb's unauthenticated explorer allows up to 100 requests/day and has a 6/minute burst limit; GrimeQuest uses stricter internal ceilings. EAN-Suche's public service allows 60 requests/hour/IP and requires a visible provider backlink for public/commercial use; GrimeQuest links the exact source and this notice.

An optional operator-configured [Serper](https://serper.dev/) Google-backed search is used only if both community and secondary structured catalogs miss the exact barcode. It is disabled without the server-side `GQ_SERPER_API_KEY`. It never scrapes third-party pages or uploads images. Only candidate titles containing the exact GTIN in the returned title/snippet are offered, and the user must check the physical product. Provider data, availability, licensing and limits are controlled by their respective owners. None of these sources is merged with GrimeQuest's reviewed cleaning-safety catalog.
