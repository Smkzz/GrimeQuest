"""Small auditable policy, deliberately narrower than general cleaning advice."""
from datetime import date
from pathlib import Path
import json
from .models import Attestations, Comparison

CATALOG = json.loads(Path(__file__).with_name("catalog.json").read_text())
PRODUCTS = {p["id"]: p for p in CATALOG["products"]}
POLICY_VERSION = "1.0.0"


def match_product(surface: str, soil: str, product_id: str, attestations: Attestations,
                  hazards: list[str], today: date | None = None) -> dict:
    """Known prohibitions and missing evidence never produce an allowed result."""
    def no(status, code, reason):
        return {"status": status, "code": code, "reason": reason, "product_id": product_id}
    if any(h != "none" for h in hazards):
        return no("blocked", "HAZARD", "A possible hazard was identified. This job is outside the prototype's scope.")
    if surface in {"unknown", "other"}:
        return no("uncertain", "SURFACE_UNSUPPORTED", "The reviewed product catalog cannot verify this material. An independent guided method is not a product recommendation.")
    if soil in {"unknown", "limescale"}:
        return no("uncertain", "SOIL_UNSUPPORTED", "This soil needs a procedure that is not in the reviewed catalog.")
    product = PRODUCTS.get(product_id)
    if not product or not product["enabled"]:
        return no("uncertain", "PRODUCT_UNREVIEWED", "No reviewed entry for this exact product. A scanned label alone does not establish suitability.")
    if (today or date.today()) > date.fromisoformat(CATALOG["valid_until"]):
        return no("uncertain", "CATALOG_STALE", "The reference catalog needs review before it can suggest products.")
    if surface in product["excluded"] or surface not in product["surfaces"]:
        return no("blocked", "OUTSIDE_SCOPE", "This product is not enabled for the selected surface. This is not a claim that it is chemically incompatible.")
    if soil not in product["soils"]:
        return no("uncertain", "NO_SOIL_EVIDENCE", "The catalog does not establish this product as a match for that visible soil.")
    if not all(attestations.model_dump().values()):
        return no("uncertain", "CONFIRMATIONS_REQUIRED", "Confirm the exact bottle, current label, surface care, absence of other cleaners and a cool, safe target.")
    return {"status": "eligible", "code": "LABEL_MATCH", "reason": "Conditional label match within this prototype's narrow scope. Follow the current package and surface-care instructions.", "product_id": product_id, "source": product["source"], "steps": product["steps"]}


def adjudicate(c: Comparison) -> dict:
    """Translate observations to game state; never measure hygiene or percentages."""
    if not c.same_target or not c.comparable or c.wet_or_glare or c.obstructed:
        return {"status": "unverifiable", "xp": 0, "reason": "The views cannot be compared reliably. Match the angle and lighting, show the entire target and photograph it dry."}
    if not c.visible_soil_before:
        return {"status": "unverifiable", "xp": 0, "reason": "The before photo does not establish a visible cleaning target."}
    if c.residue_after == "uncertain" or c.improvement == "uncertain":
        return {"status": "unverifiable", "xp": 0, "reason": "Visible change is uncertain. No clear result or XP is claimed."}
    if c.residue_after == "not_visible" and c.improvement == "substantial":
        return {"status": "clear", "xp": 300, "reason": "The model reports substantial visible improvement in comparable views. This is not proof of hygiene, disinfection or who performed the task."}
    return {"status": "partial", "xp": 0, "reason": "A complete visual clear was not established. Visible residue may remain. Do not switch or add products to chase points."}
