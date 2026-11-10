"""Admission gate for the L02 observer capability contract.

This is a source-free research gate.  It does not create an owner mask and it
does not score a candidate.  Its only job is to stop a broad semantic parser
from being disguised as an outerwear/underlayer/occlusion observer and then
patched into a formal candidate with local rules.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


class ObserverCapabilityHold(ValueError):
    """Raised when the observer cannot be admitted to a formal probe."""


REQUIRED_CAPABILITIES = frozenset(
    {
        "outerwear",
        "underlayer",
        "sleeve",
        "arm",
        "occlusion_relation",
        "instance_grouping",
    }
)


@dataclass(frozen=True)
class ObserverCapabilitySpec:
    observer_id: str
    revision: str
    weights_sha256: str
    output_contract: tuple[str, ...]
    source_only: bool = True


def _normalise_contract(values: Iterable[str]) -> frozenset[str]:
    if isinstance(values, (str, bytes)):
        raise ObserverCapabilityHold("INVALID_OUTPUT_CONTRACT")
    contract = frozenset(values)
    if not contract or any(not isinstance(item, str) or not item for item in contract):
        raise ObserverCapabilityHold("INVALID_OUTPUT_CONTRACT")
    return contract


def assess_observer_capability(spec: ObserverCapabilitySpec) -> dict[str, object]:
    """Return a deterministic admission result without touching image data."""
    if not isinstance(spec, ObserverCapabilitySpec):
        raise ObserverCapabilityHold("INVALID_OBSERVER_SPEC")
    if not spec.observer_id or not spec.revision:
        raise ObserverCapabilityHold("INVALID_OBSERVER_IDENTITY")
    if not re.fullmatch(r"[0-9a-f]{64}", spec.weights_sha256):
        raise ObserverCapabilityHold("UNSIGNED_OR_UNPINNED_WEIGHTS")
    if spec.source_only is not True:
        raise ObserverCapabilityHold("NON_SOURCE_ONLY_OBSERVER")

    contract = _normalise_contract(spec.output_contract)
    missing = tuple(sorted(REQUIRED_CAPABILITIES - contract))
    if missing:
        return {
            "status": "CAPABILITY_HOLD",
            "observer_id": spec.observer_id,
            "revision": spec.revision,
            "missing_capabilities": missing,
            "observed_capabilities": tuple(sorted(contract)),
            "formal_probe_allowed": False,
            "reason": "observer output cannot distinguish every required semantic boundary",
        }
    return {
        "status": "CAPABILITY_PASS_RESEARCH_ONLY",
        "observer_id": spec.observer_id,
        "revision": spec.revision,
        "missing_capabilities": (),
        "observed_capabilities": tuple(sorted(contract)),
        "formal_probe_allowed": True,
        "reason": "capability contract is present; Phase4 and owner authority remain separate gates",
    }


def see_through_bodypart_spec(*, weights_sha256: str) -> ObserverCapabilitySpec:
    """Describe the currently used See-through body-part checkpoint.

    The labels are deliberately limited to the model's published body-part
    output.  No inferred outer/underlayer or instance capability is added.
    """
    return ObserverCapabilitySpec(
        observer_id="see-through-bodypart-parser",
        revision="df019de5129d6c4b406587a14c3501669441a783",
        weights_sha256=weights_sha256,
        output_contract=(
            "hair",
            "headwear",
            "face",
            "eyes",
            "eyewear",
            "ears",
            "earwear",
            "nose",
            "mouth",
            "neck",
            "neckwear",
            "topwear",
            "handwear",
            "bottomwear",
            "legwear",
            "footwear",
            "tail",
            "wings",
            "objects",
        ),
    )
