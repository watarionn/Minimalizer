import json

import pytest

from minimalizer_zerobase.production import (
    LEGACY_ROUTE,
    ZEROBASE2_ROUTE,
    ProductionRouteSwitch,
    compare_production_output,
    phase14_authorizes_production,
)


def closure():
    return {
        "phase": 14,
        "pass": True,
        "next_phase_authorized": 15,
        "gates": {
            "diagnostic2_zero_base_visual": {"pass": True},
            "approved18_production_regression": {"pass": True},
            "approved78_formal_migration": {"pass": True},
        },
    }


def test_phase14_closure_authorizes_zerobase2():
    payload = closure()
    assert phase14_authorizes_production(payload)
    decision = ProductionRouteSwitch(ZEROBASE2_ROUTE).decide(payload)
    assert decision.active_route == ZEROBASE2_ROUTE
    assert decision.rollback_available
    assert decision.rollback_reason is None


def test_failed_phase14_gate_rolls_back_to_minimalizer2():
    payload = closure()
    payload["gates"]["approved18_production_regression"]["pass"] = False
    decision = ProductionRouteSwitch(ZEROBASE2_ROUTE).decide(payload)
    assert decision.active_route == LEGACY_ROUTE
    assert not decision.zerobase_authorized
    assert decision.rollback_reason == "phase14-final-gate-not-authorized"


def test_default_route_preserves_existing_production(monkeypatch):
    monkeypatch.delenv("MINIMALIZER_PRODUCTION_ROUTE", raising=False)
    decision = ProductionRouteSwitch().decide(closure())
    assert decision.requested_route == LEGACY_ROUTE
    assert decision.active_route == LEGACY_ROUTE


def test_unknown_route_fails_closed():
    with pytest.raises(ValueError, match="unsupported production route"):
        ProductionRouteSwitch("surprise-route")


def test_production_compare_requires_pixel_and_metadata_match(tmp_path):
    dev = tmp_path / "dev.png"
    prod = tmp_path / "prod.png"
    dev.write_bytes(b"same-pixels")
    prod.write_bytes(b"same-pixels")
    result = compare_production_output(
        dev, prod,
        {"profile": "balanced", "elapsed_ms": 10},
        {"profile": "balanced", "elapsed_ms": 99, "route": "zerobase2"},
    )
    assert result["pass"]
    prod.write_bytes(b"different")
    result = compare_production_output(
        dev, prod, {"profile": "balanced"}, {"profile": "balanced"}
    )
    assert not result["pass"]
    assert not result["pixel_match"]
