from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from .alpha_contract import BackgroundMode, resolve_alpha_background_route
from .output_contract import build_output_format_compatibility

BrowserMode = Literal["standard", "rinka_reference", "color_strip"]
BrowserRoute = Literal["v2", "legacy"]
BrowserRolloutState = Literal[
    "legacy_default",
    "v2_standard_opt_in",
    "v2_standard_default",
]
BROWSER_MIGRATION_SCHEMA_VERSION = "minimalizer-v2-browser-migration-v1"


@dataclass(frozen=True, slots=True)
class BrowserRolloutStage:
    state: BrowserRolloutState
    standard_default_route: BrowserRoute
    explicit_v2_selector: bool
    description: str


@dataclass(frozen=True, slots=True)
class BrowserMigrationContract:
    schema_version: str
    current_state: BrowserRolloutState
    legacy_endpoint: str
    v2_endpoint: str
    specialized_modes: tuple[str, ...]
    rollback_target: BrowserRolloutState
    rollback_requires_data_migration: bool
    automatic_error_fallback: bool
    stages: tuple[BrowserRolloutStage, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "current_state": self.current_state,
            "legacy_endpoint": self.legacy_endpoint,
            "v2_endpoint": self.v2_endpoint,
            "specialized_modes": list(self.specialized_modes),
            "rollback_target": self.rollback_target,
            "rollback_requires_data_migration": self.rollback_requires_data_migration,
            "automatic_error_fallback": self.automatic_error_fallback,
            "stages": [asdict(item) for item in self.stages],
        }


def _web_output_route(output_format: str) -> BrowserRoute:
    report = build_output_format_compatibility()
    for item in report.policies:
        if item.surface == "web" and item.output_format == output_format:
            return item.route_on_v2_default
    return "legacy"

def resolve_browser_route(
    *,
    rollout_state: BrowserRolloutState,
    mode: BrowserMode,
    output_format: str,
    background_mode: BackgroundMode = "white",
    source_has_transparency: bool = False,
    ignore_source_alpha: bool = False,
    user_selected_v2: bool = False,
) -> BrowserRoute:
    if mode != "standard":
        return "legacy"
    if rollout_state == "legacy_default":
        return "legacy"
    if rollout_state == "v2_standard_opt_in" and not user_selected_v2:
        return "legacy"
    if _web_output_route(output_format) != "v2":
        return "legacy"
    return resolve_alpha_background_route(
        background_mode=background_mode,
        source_has_transparency=source_has_transparency,
        ignore_source_alpha=ignore_source_alpha,
    )


def build_browser_migration_contract() -> BrowserMigrationContract:
    stages = (
        BrowserRolloutStage(
            "legacy_default",
            "legacy",
            False,
            "Current production browser behavior; all modes stay on /api/minimalize.",
        ),
        BrowserRolloutStage(
            "v2_standard_opt_in",
            "legacy",
            True,
            "Standard mode may expose an explicit V2 selector; specialized modes remain legacy.",
        ),
        BrowserRolloutStage(
            "v2_standard_default",
            "v2",
            True,
            "Eligible Standard PNG requests default to V2; incompatible requests and specialized modes stay legacy.",
        ),
    )
    return BrowserMigrationContract(
        schema_version=BROWSER_MIGRATION_SCHEMA_VERSION,
        current_state="v2_standard_default",
        legacy_endpoint="/api/minimalize",
        v2_endpoint="/api/v2/minimalize",
        specialized_modes=("rinka_reference", "color_strip"),
        rollback_target="legacy_default",
        rollback_requires_data_migration=False,
        automatic_error_fallback=False,
        stages=stages,
    )
