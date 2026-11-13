"""Source-only anime body-part owner candidate construction.

This research layer consumes two independently generated observation maps:
See-through anime body-part logits and Sapiens2 body-part class IDs.  It does
not consume human labels, review JSON, frozen owners, or case-specific rules.
The returned owner is a candidate only; it is never Phase4 or production
authority.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


class AnimeBodypartOwnerHold(ValueError):
    """Raised when the source-only observation contract is invalid."""


SEE_THROUGH_BODY_PARTS = (
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
)

# Sapiens2 DOME-29 IDs for hands and arm segments.  These are taxonomy
# constants, not labels supplied by the user or fitted to a reviewed case.
SAPIENS2_ARM_CLASS_IDS = frozenset({6, 7, 11, 15, 16, 20})


@dataclass(frozen=True)
class AnimeBodypartOwnerCandidate:
    owner: np.ndarray
    unknown: np.ndarray
    topwear_observed: np.ndarray
    handwear_observed: np.ndarray
    arm_observed: np.ndarray

    @property
    def source_only(self) -> bool:
        return True

    @property
    def unknown_not_treated_as_negative(self) -> bool:
        return True

    @property
    def owner_promotion_authorized(self) -> bool:
        return False


def _validate_inputs(
    see_through_logits: np.ndarray,
    sapiens_class_ids: np.ndarray,
    source_alpha: np.ndarray,
) -> None:
    if (
        not isinstance(see_through_logits, np.ndarray)
        or see_through_logits.ndim != 3
        or see_through_logits.shape[0] != len(SEE_THROUGH_BODY_PARTS)
        or not np.issubdtype(see_through_logits.dtype, np.floating)
        or not np.isfinite(see_through_logits).all()
    ):
        raise AnimeBodypartOwnerHold("INVALID_SEE_THROUGH_LOGITS")
    if (
        not isinstance(sapiens_class_ids, np.ndarray)
        or sapiens_class_ids.ndim != 2
        or sapiens_class_ids.dtype != np.uint8
    ):
        raise AnimeBodypartOwnerHold("INVALID_SAPIENS_CLASS_IDS")
    if (
        not isinstance(source_alpha, np.ndarray)
        or source_alpha.ndim != 2
        or source_alpha.dtype != np.bool_
    ):
        raise AnimeBodypartOwnerHold("INVALID_SOURCE_ALPHA")
    shape = see_through_logits.shape[1:]
    if sapiens_class_ids.shape != shape or source_alpha.shape != shape:
        raise AnimeBodypartOwnerHold("OBSERVATION_SHAPE_MISMATCH")


def build_anime_bodypart_owner_candidate(
    *,
    see_through_logits: np.ndarray,
    sapiens_class_ids: np.ndarray,
    source_alpha: np.ndarray,
) -> AnimeBodypartOwnerCandidate:
    """Build one whole-image candidate from fixed anime/body observations.

    The rule keeps See-through ``topwear`` and promotes only ``handwear``
    pixels not observed as Sapiens2 hand/arm pixels.  Pixels without a
    positive observation remain unknown and are never converted to negative.
    """

    _validate_inputs(see_through_logits, sapiens_class_ids, source_alpha)
    topwear = (see_through_logits[11] > 0) & source_alpha
    handwear = (see_through_logits[12] > 0) & source_alpha
    arm = np.isin(sapiens_class_ids, tuple(SAPIENS2_ARM_CLASS_IDS)) & source_alpha

    owner = source_alpha & (topwear | (handwear & ~arm))
    unknown = source_alpha & ~owner
    if np.any(owner & unknown):
        raise AnimeBodypartOwnerHold("OWNER_UNKNOWN_OVERLAP")
    if np.any(owner & ~source_alpha):
        raise AnimeBodypartOwnerHold("OWNER_OUTSIDE_SOURCE_ALPHA")

    return AnimeBodypartOwnerCandidate(
        owner=owner.astype(np.uint8, copy=False),
        unknown=unknown,
        topwear_observed=topwear,
        handwear_observed=handwear,
        arm_observed=arm,
    )
