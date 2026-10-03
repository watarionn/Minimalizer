from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

LEGACY_ROUTE = "minimalizer2"
ZEROBASE2_ROUTE = "zerobase2"
ROUTE_ENV = "MINIMALIZER_PRODUCTION_ROUTE"


@dataclass(frozen=True)
class ProductionRouteDecision:
    requested_route: str
    active_route: str
    zerobase_authorized: bool
    rollback_available: bool
    rollback_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load_object(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def phase14_authorizes_production(payload: dict[str, Any]) -> bool:
    gates = payload.get("gates", {})
    required = (
        "diagnostic2_zero_base_visual",
        "approved18_production_regression",
        "approved78_formal_migration",
    )
    return bool(
        payload.get("phase") == 14
        and payload.get("pass") is True
        and payload.get("next_phase_authorized") == 15
        and isinstance(gates, dict)
        and all(
            isinstance(gates.get(name), dict)
            and gates[name].get("pass") is True
            for name in required
        )
    )


class ProductionRouteSwitch:
    def __init__(self, requested_route: str | None = None):
        route = (requested_route or os.getenv(ROUTE_ENV, LEGACY_ROUTE)).strip()
        if route not in {LEGACY_ROUTE, ZEROBASE2_ROUTE}:
            raise ValueError(f"unsupported production route: {route}")
        self.requested_route = route

    def decide(self, phase14_closure: dict[str, Any]) -> ProductionRouteDecision:
        authorized = phase14_authorizes_production(phase14_closure)
        if self.requested_route == ZEROBASE2_ROUTE and not authorized:
            return ProductionRouteDecision(
                requested_route=ZEROBASE2_ROUTE,
                active_route=LEGACY_ROUTE,
                zerobase_authorized=False,
                rollback_available=True,
                rollback_reason="phase14-final-gate-not-authorized",
            )
        return ProductionRouteDecision(
            requested_route=self.requested_route,
            active_route=self.requested_route,
            zerobase_authorized=authorized,
            rollback_available=True,
        )
def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_production_output(
    development_output: str | Path,
    production_output: str | Path,
    development_metadata: dict[str, Any],
    production_metadata: dict[str, Any],
) -> dict[str, Any]:
    dev_sha = sha256_file(development_output)
    prod_sha = sha256_file(production_output)
    ignored = {"elapsed_ms", "route", "processing_ms"}
    dev_meta = {
        key: value for key, value in development_metadata.items()
        if key not in ignored
    }
    prod_meta = {
        key: value for key, value in production_metadata.items()
        if key not in ignored
    }
    pixel_match = dev_sha == prod_sha
    metadata_match = dev_meta == prod_meta
    return {
        "pixel_match": pixel_match,
        "metadata_match": metadata_match,
        "development_sha256": dev_sha,
        "production_sha256": prod_sha,
        "pass": pixel_match and metadata_match,
    }


def load_phase14_closure(path: str | Path) -> dict[str, Any]:
    return _load_object(path)
