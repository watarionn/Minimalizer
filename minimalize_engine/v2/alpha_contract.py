from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

AlphaRoute = Literal["v2", "legacy"]
BackgroundMode = Literal["source", "white", "transparent", "custom"]
ALPHA_BACKGROUND_SCHEMA_VERSION = "minimalizer-v2-alpha-background-v1"


@dataclass(frozen=True, slots=True)
class AlphaBackgroundPolicy:
    condition: str
    route_on_v2_default: AlphaRoute
    rationale: str


@dataclass(frozen=True, slots=True)
class AlphaBackgroundCompatibilityReport:
    schema_version: str
    v2_native_background: str
    v2_native_alpha: str
    preserves_opaque_white_pixels: bool
    preserves_legacy_alpha_features: bool
    policies: tuple[AlphaBackgroundPolicy, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "v2_native_background": self.v2_native_background,
            "v2_native_alpha": self.v2_native_alpha,
            "preserves_opaque_white_pixels": self.preserves_opaque_white_pixels,
            "preserves_legacy_alpha_features": self.preserves_legacy_alpha_features,
            "policies": [asdict(item) for item in self.policies],
        }


def resolve_alpha_background_route(
    *,
    background_mode: BackgroundMode,
    source_has_transparency: bool,
    ignore_source_alpha: bool = False,
) -> AlphaRoute:
    if ignore_source_alpha:
        return "legacy"
    if background_mode != "white":
        return "legacy"
    if source_has_transparency:
        return "legacy"
    return "v2"


def build_alpha_background_compatibility() -> AlphaBackgroundCompatibilityReport:
    policies = (
        AlphaBackgroundPolicy(
            "opaque source + white background",
            "v2",
            "This exactly matches the current V2 RGB renderer and keeps canonical opaque output unchanged.",
        ),
        AlphaBackgroundPolicy(
            "source contains material transparency",
            "legacy",
            "Retain source-alpha masking and subject-cutout behavior on the established legacy path.",
        ),
        AlphaBackgroundPolicy(
            "background=source",
            "legacy",
            "Retain source-derived background color selection instead of pretending V2 white canvas has identical semantics.",
        ),
        AlphaBackgroundPolicy(
            "background=transparent",
            "legacy",
            "Retain transparent output on the existing alpha-capable renderer.",
        ),
        AlphaBackgroundPolicy(
            "background=custom",
            "legacy",
            "Retain explicit custom background colors on the legacy renderer until V2 exposes an equivalent contract.",
        ),
        AlphaBackgroundPolicy(
            "ignore-source-alpha requested",
            "legacy",
            "Retain the legacy ignore-alpha semantics rather than silently changing how hidden RGB is interpreted.",
        ),
    )
    return AlphaBackgroundCompatibilityReport(
        schema_version=ALPHA_BACKGROUND_SCHEMA_VERSION,
        v2_native_background="white RGB canvas",
        v2_native_alpha="file adapter composites RGBA onto white; renderer emits opaque RGB PNG",
        preserves_opaque_white_pixels=True,
        preserves_legacy_alpha_features=True,
        policies=policies,
    )
