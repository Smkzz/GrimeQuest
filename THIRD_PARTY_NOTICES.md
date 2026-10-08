# Third-party notices

Original application code and fixture illustrations use the MIT license in LICENSE. Product names identify real catalog variants; no affiliation or endorsement is implied. Product reference descriptions are narrow paraphrases with links to manufacturer guidance. Do not assume trademark rights or a right to redistribute full product labels.

Runtime dependencies include FastAPI (MIT), Starlette (BSD-3-Clause), Uvicorn (BSD-3-Clause), Pydantic (MIT), HTTPX (BSD-3-Clause) and Pillow (HPND). Development dependencies include TypeScript (Apache-2.0), pytest (MIT), pytest-cov (MIT) and Playwright (Apache-2.0). Their transitive dependencies retain their own notices and licenses. Dependencies are installed separately, not bundled in the source ZIP. Review current package license files before redistributing binaries.

System fonts are referenced by CSS; no font files are distributed. SVG/PNG practice scenes and the mascot/icon geometry are original, not photographs of a real cleaning result.

Official implementation references are linked inline in README, SECURITY and SAFETY. The TypeScript 5.8.3 package integrity was read from the official npm package metadata. Manual CI action pins were verified against the corresponding official action release commits on 2026-10-06; being pinned does not certify that a dependency is vulnerability-free.

The self-hosted desktop QR code encoder includes **qr-creator** (Copyright © 2017 The Nimiq Foundation, MIT), derived from jquery-qrcode (Lars Jung, MIT) and the JavaScript QR Code Generator (Kazuhiko Arase, MIT). The vendored browser source has its ES-module export removed to run under the existing self-hosted, no-inline-script CSP. Its original license is preserved in `web/vendor/qr-creator.LICENSE.txt`. There is no third-party QR or tracking endpoint.

Local optical character recognition uses the Debian-provided **Tesseract OCR** engine (Apache-2.0), Leptonica image processing library (BSD-2-Clause), and Finnish/English Tesseract traineddata (Apache-2.0). Packages are installed from the distribution at image-build time, with no model-provider network calls at runtime. OCR outputs are unverified transcriptions and cannot create chemical-use permissions.
