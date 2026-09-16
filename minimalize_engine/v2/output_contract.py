from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

OutputSurface = Literal["web", "cli"]
OutputRoute = Literal["v2", "legacy"]
OUTPUT_FORMAT_SCHEMA_VERSION = "minimalizer-v2-output-format-v1"


@dataclass(frozen=True, slots=True)
class OutputFormatPolicy:
    surface: OutputSurface
    output_format: str
    route_on_v2_default: OutputRoute
    media_type: str
    rationale: str


@dataclass(frozen=True, slots=True)
class OutputFormatCompatibilityReport:
    schema_version: str
    preserves_current_default: bool
    policies: tuple[OutputFormatPolicy, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "preserves_current_default": self.preserves_current_default,
            "policies": [asdict(item) for item in self.policies],
        }


def build_output_format_compatibility() -> OutputFormatCompatibilityReport:
    policies = (
        OutputFormatPolicy(
            "web", "png", "v2", "image/png",
            "Use the deterministic minimalizer-v2-png-v1 export when the standard default migrates.",
        ),
        OutputFormatPolicy(
            "web", "svg", "legacy", "image/svg+xml",
            "Retain the existing vector SVG route; V2 does not claim an SVG contract.",
        ),
        OutputFormatPolicy(
            "cli", "png", "v2", "image/png",
            "PNG output may use the deterministic V2 PNG contract after default migration.",
        ),
        OutputFormatPolicy(
            "cli", "svg", "legacy", "image/svg+xml",
            "Retain the existing CLI SVG renderer rather than changing vector semantics.",
        ),
        OutputFormatPolicy(
            "cli", "webp", "legacy", "image/webp",
            "Retain the existing CLI WEBP renderer; no V2 WEBP contract is asserted.",
        ),
    )
    return OutputFormatCompatibilityReport(
        schema_version=OUTPUT_FORMAT_SCHEMA_VERSION,
        preserves_current_default=True,
        policies=policies,
    )
