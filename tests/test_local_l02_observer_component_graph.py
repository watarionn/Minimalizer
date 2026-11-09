from __future__ import annotations

import hashlib

import numpy as np
import pytest

from tools.research.local_l02_observer_component_graph import (
    ObserverComponentGraphHold,
    ObserverMask,
    build_observer_component_graph,
)


def _observer(name: str, role: str, mask: np.ndarray) -> ObserverMask:
    return ObserverMask(
        name=name,
        role=role,
        mask=mask,
        expected_sha256=hashlib.sha256(mask.tobytes()).hexdigest(),
        model_id=name,
    )


def test_graph_holds_a_conflicting_component_as_one_unit():
    alpha = np.ones((8, 9), dtype=bool)
    garment = np.zeros((8, 9), dtype=np.uint8)
    arm = np.zeros((8, 9), dtype=np.uint8)
    garment[1:4, 1:4] = 1
    arm[3:6, 3:6] = 1

    graph = build_observer_component_graph(
        source_alpha=alpha,
        observers=(_observer("garment-model", "garment", garment), _observer("arm-model", "arm", arm)),
    )

    assert graph.source_only is True
    assert graph.human_labels_used is False
    assert graph.owner_arrays_used is False
    assert graph.unknown_not_treated_as_negative is True
    assert len(graph.components) == 1
    assert graph.components[0].decision == "ROLE_CONFLICT"
    assert graph.components[0].area == 17
    assert int(graph.unknown.sum()) == 72 - 17


def test_missing_observation_is_unknown_not_negative():
    alpha = np.ones((5, 5), dtype=bool)
    observer = np.zeros((5, 5), dtype=np.uint8)
    observer[1:3, 1:3] = 1

    graph = build_observer_component_graph(
        source_alpha=alpha,
        observers=(_observer("one", "garment", observer),),
    )

    assert graph.observed_pixels == 4
    assert graph.unknown_pixels == 21
    assert int(graph.unknown.sum()) == 21


def test_observer_hash_mismatch_fails_closed():
    alpha = np.ones((3, 3), dtype=bool)
    mask = np.ones((3, 3), dtype=np.uint8)
    bad = ObserverMask("one", "garment", mask, "0" * 64, "model")

    with pytest.raises(ObserverComponentGraphHold, match="INVALID_OBSERVER_ENTRY"):
        build_observer_component_graph(source_alpha=alpha, observers=(bad,))
