"""Strict trust-boundary schemas. Model output is evidence, never authority."""
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, BeforeValidator

Surface = Literal["uncoated_glass", "glazed_ceramic", "stainless_steel", "glass_ceramic_hob", "natural_stone", "wood", "unknown"]
Soil = Literal["grease", "fingerprints", "light_grime", "limescale", "unknown"]
Hazard = Literal["heat", "electrical", "mould", "body_fluid", "unknown_chemical", "damage", "none"]
ShortText = Annotated[str, Field(min_length=1, max_length=240)]
ImageData = Annotated[str, Field(min_length=32, max_length=2_800_000)]

def require_explicit_true(value):
    # Literal[True] alone also accepts JSON 1 / 1.0 in Pydantic. Consent must not.
    if value is not True:
        raise ValueError("Explicit boolean true is required")
    return value

ExplicitConsent = Annotated[Literal[True], BeforeValidator(require_explicit_true)]

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

class Box(StrictModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)
    width: float = Field(gt=0, le=1)
    height: float = Field(gt=0, le=1)

    @model_validator(mode="after")
    def bounds(self):
        if self.x + self.width > 1.001 or self.y + self.height > 1.001:
            raise ValueError("Target box must fit in the image")
        return self

class TargetAnalysis(StrictModel):
    object_name: ShortText
    surface: Surface
    soil: Soil
    visible_soil: bool
    image_quality: Literal["usable", "unusable"]
    material_certainty: Literal["tentative", "unknown"]
    hazards: list[Hazard] = Field(min_length=1, max_length=6)
    target_box: Box

class ProductObservation(StrictModel):
    name: ShortText
    label_readable: bool
    label_text: str = Field(max_length=6000)
    warnings_observed: list[ShortText] = Field(max_length=12)
    # No "safe_surfaces" field: text extraction cannot mint permissions.

class Comparison(StrictModel):
    same_target: bool
    comparable: bool
    visible_soil_before: bool
    residue_after: Literal["not_visible", "reduced", "present", "uncertain"]
    improvement: Literal["substantial", "some", "none", "uncertain"]
    wet_or_glare: bool
    obstructed: bool

class ImageRequest(StrictModel):
    image: ImageData
    consent: ExplicitConsent

class BarcodeRequest(StrictModel):
    barcode: str = Field(min_length=8, max_length=14)


class ProductRequest(StrictModel):
    front_image: ImageData
    back_image: ImageData
    consent: ExplicitConsent

class Attestations(StrictModel):
    exact_product: bool
    label_allows_target: bool
    surface_care_allows: bool
    no_other_product: bool
    cool_and_safe: bool

class StartRequest(StrictModel):
    target_ticket: str = Field(min_length=20, max_length=12000)
    surface: Surface
    soil: Soil
    product_id: str = Field(min_length=1, max_length=80)
    attestations: Attestations

class VerifyRequest(StrictModel):
    encounter_ticket: str = Field(min_length=20, max_length=14000)
    before_image: ImageData
    after_image: ImageData
    consent: ExplicitConsent
    procedure_completed: ExplicitConsent
    surface_dry: ExplicitConsent

class MatchRequest(StrictModel):
    surface: Surface
    soil: Soil
    product_id: str = Field(min_length=1, max_length=80)
    attestations: Attestations
    hazards: list[Hazard] = Field(max_length=6)
