"""Release gate: every known surface is represented; reviewed cleaner permissions stay narrow.

This checks server trust boundaries without pytest, network access or provider calls.
The independent guided flow is checked by the Node/Playwright suites.
"""
from datetime import date
from typing import get_args

from server.models import Surface, Soil, Attestations
from server.policy import PRODUCTS, match_product

SURFACES = {
    "uncoated_glass", "glazed_ceramic", "stainless_steel", "glass_ceramic_hob",
    "natural_stone", "wood", "other", "unknown",
}
assert set(get_args(Surface)) == SURFACES
assert set(get_args(Soil)) == {"grease", "fingerprints", "light_grime", "limescale", "unknown"}
a = Attestations(
    exact_product=True, label_allows_target=True, surface_care_allows=True,
    no_other_product=True, cool_and_safe=True,
)
today = date(2026, 10, 8)

# A playable, user-checked material is NOT a catalog product authorization.
for surf in ("stainless_steel", "glass_ceramic_hob", "natural_stone", "wood", "other"):
    for soil in get_args(Soil):
        for product in PRODUCTS:
            claim = match_product(surf, soil, product, a, ["none"], today)
            assert claim["status"] != "eligible", (surf, soil, product, claim)
for product in PRODUCTS:
    for surf in get_args(Surface):
        report = match_product(surf, "light_grime", product, a, ["heat"], today)
        assert report["status"] == "blocked" and report["code"] == "HAZARD"
for surf in ("other", "unknown"):
    claim = match_product(surf, "light_grime", next(iter(PRODUCTS)), a, ["none"], today)
    assert claim["code"] == "SURFACE_UNSUPPORTED"
assert match_product("glazed_ceramic", "grease", "method-kitchen-clementine-uk-828", a,
                     ["none"], today)["status"] == "eligible"
print("GQ_GUIDED_SURFACES_POLICY_ISOLATION_NO_NETWORK_PASS")
