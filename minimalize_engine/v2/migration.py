from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

MigrationStatus = Literal["ready", "blocked", "out_of_scope"]
MIGRATION_SCHEMA_VERSION = "minimalizer-v2-migration-v1"


@dataclass(frozen=True, slots=True)
class MigrationItem:
    id: str
    area: str
    status: MigrationStatus
    legacy_contract: str
    v2_contract: str
    required_action: str | None = None


@dataclass(frozen=True, slots=True)
class MigrationReadinessReport:
    schema_version: str
    scope: str
    items: tuple[MigrationItem, ...]

    @property
    def blockers(self) -> tuple[MigrationItem, ...]:
        return tuple(item for item in self.items if item.status == "blocked")

    @property
    def ready_for_default(self) -> bool:
        return not self.blockers
    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "scope": self.scope,
            "ready_for_default": self.ready_for_default,
            "blocker_count": len(self.blockers),
            "blocker_ids": [item.id for item in self.blockers],
            "items": [asdict(item) for item in self.items],
        }


def build_migration_readiness() -> MigrationReadinessReport:
    items = (
        MigrationItem(
            "canonical_quality", "quality", "ready",
            "legacy default remains active",
            "V2 canonical 18-case hard invariants pass 18/18",
        ),
        MigrationItem(
            "deterministic_png", "export", "ready",
            "legacy PNG encoding is exporter-dependent",
            "minimalizer-v2-png-v1 is deterministic and hash-addressable",
        ),
        MigrationItem(
            "entry_point_boundary", "integration", "ready",
            "legacy Web/CLI default paths remain unchanged",
            "V2 opt-in Web endpoint and CLI shadow preserve Phase G bytes",
        ),
        MigrationItem(
            "web_control_mapping", "web", "ready",
            "standard mode exposes level, colors, max_shapes, background, and svg/png",
            "Phase P matrix exhaustively classifies the exposed legacy Web controls as mapped, legacy-retained, or out of scope",
        ),
        MigrationItem(
            "output_format_parity", "export", "ready",
            "Web supports SVG/PNG; CLI supports SVG plus optional PNG/WEBP",
            "Phase Q routes PNG to the deterministic V2 contract while retaining SVG/WEBP on the legacy renderers",
        ),
        MigrationItem(
            "alpha_background_parity", "image_io", "ready",
            "legacy supports source/white/transparent/custom backgrounds and alpha controls",
            "Phase R uses V2 only for opaque white-background requests and retains every alpha-sensitive/background-specific request on the legacy renderer",
        ),
        MigrationItem(
            "cli_control_mapping", "cli", "ready",
            "legacy CLI exposes level/detail, composition, cleanup, character, face, hand, and debug switches",
            "Phase P matrix exhaustively classifies every legacy CLI control as mapped or legacy-retained",
        ),
        MigrationItem(
            "browser_ui_migration", "web_ui", "blocked",
            "browser workspace submits only legacy modes to /api/minimalize",
            "V2 is API-only opt-in and intentionally absent from the browser UI",
            "Design an explicit migration/rollback UI contract before changing the default.",
        ),
        MigrationItem(
            "performance_budget", "operations", "blocked",
            "legacy default has established hosted behavior",
            "V2 has regression timings but no default-migration latency budget",
            "Define and pass a representative latency/resource budget before migration.",
        ),
        MigrationItem(
            "special_modes", "scope", "out_of_scope",
            "Rinka Reference and Color Strip are separate legacy Web modes",
            "Phase I targets only the standard-engine default",
            "Keep specialized modes separately routed during standard-engine migration.",
        ),
    )
    return MigrationReadinessReport(
        schema_version=MIGRATION_SCHEMA_VERSION,
        scope="legacy_standard_default_to_v2",
        items=items,
    )
