# Activate GrimeQuest Cloud Vision OCR — operator only

This runbook is for the GrimeQuest operator, **not players**. No player needs a Google account, an API key, or server settings.

## Status and billing

The code uses synchronous Google Cloud Vision at the **EU** regional endpoint. It was tested with mocked Vision responses only. Each consented scan sends two images in a single API batch: front TEXT_DETECTION and directions/warnings DOCUMENT_TEXT_DETECTION. Each feature/image is a billable unit.

Google currently lists the first 1,000 Cloud Vision image-feature units/month as free; a two-image scan uses two units. This is not a spending cap and the allowance may be shared with other project activity. The app rate-limits to six scans/hour and twelve scans/24 hours **per process**, but deploy restarts reset these counts. A billing alert alone does not cap charges.

## Operator setup (one time, not in the app)

1. In [Google Cloud Console](https://console.cloud.google.com/), create/select a dedicated **billing-enabled** project for this service.
2. [Enable the Cloud Vision API](https://console.cloud.google.com/apis/library/vision.googleapis.com) in that project.
3. In [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials), create an API key restricted to **Cloud Vision API only**. Never paste the key into GitHub, public chat or frontend JavaScript. Backend uses the HTTPS x-goog-api-key header, not a URL query.
4. Configure restrictive [Vision project quotas](https://docs.cloud.google.com/vision/quotas) and a [billing budget](https://docs.cloud.google.com/billing/docs/how-to/budgets). A billing alert alone **does not prevent spending**; ensure the owner explicitly approves the possible billed amount, and use a real spending-cap budget if supported for the account/service. Operator is responsible for controlling ongoing consumption.
5. Review the [Cloud Vision Data Usage FAQ](https://docs.cloud.google.com/vision/docs/data-usage), [Cloud Data Processing Addendum](https://cloud.google.com/terms/data-processing-addendum), GrimeQuest's privacy notice, and add confirmed service operator identity/contact/legal grounds before processing public users' photographs.
6. Configure three **Railway production service** variables (never client config):
    - GQ_GOOGLE_VISION_PROJECT_ID: your project ID (not its display name).
    - GQ_GOOGLE_VISION_API_KEY: private API key restricted to Cloud Vision API.
    - GQ_GOOGLE_VISION_ENABLED=1: operator approval after the cost/privacy/quota review.
7. Wait for the existing GrimeQuest Railway service to redeploy. Inspect the public /api/health endpoint: label_ocr_ready must be true and label_ocr_processor must read google_cloud_vision. This confirms configuration only, **not** successful Google billing or live recognition.
8. On a real iPhone Home Screen app, open Arsenal → Scan a product → Recognize both labels. After explicit consent, test both sides of a label you own. Check the returned editable text against the real package, including every warning. A recognized name remains unreviewed and must not grant a cleaning recommendation.
9. Test revoked credentials, quota limits, Google service failures and network loss. Each must safely offer manual entry without leaking secrets, retrying paid inference or losing the player's photos.

## Privacy, security and rollback

- Exactly two normalized, metadata-stripped JPEGs are sent in memory to the fixed EU region Google Cloud Vision endpoint after per-scan consent. GrimeQuest does not persist original label images, OCR transcripts or API keys in files or logs.
- According to Google, synchronous Vision photos are processed in memory and not stored to disk, and are not used to train Cloud Vision models. Google may temporarily retain request metadata.
- Provider URL is fixed to eu-vision.googleapis.com; code does not follow HTTP redirects or accept arbitrary hostnames.
- If credentials are missing or operator activation is disabled, OCR is unavailable and manual entry/guided camera gameplay work normally.
- To disable provider calls immediately, set GQ_GOOGLE_VISION_ENABLED=0 and redeploy, or revoke the key in Google Cloud. Do not erase any player local inventory.

## Source documentation

- [Cloud Vision REST authentication](https://docs.cloud.google.com/vision/docs/request)
- [Vision pricing](https://cloud.google.com/vision/pricing)
- [Cloud Vision quotas](https://docs.cloud.google.com/vision/quotas)
- [Google billing alerts vs spending caps](https://docs.cloud.google.com/billing/docs/how-to/budgets)
- [Vision data use](https://docs.cloud.google.com/vision/docs/data-usage)
