"""Research-only source-pixel preservation of class32 neutral underlayer candidates.

A conservative H06-exposed shadow, NOT a semantic classifier or owner-3
promotion. The prior frozen coat owner is unchanged except for the already
integrated hue abstention. Removed neutral source pixels are returned in a
separate *unapproved* candidate layer instead of silently disappearing.

No human labels, hand coordinates, image generation or private data are inputs.
Only the signed original RGBA, frozen model class IDs and frozen owner are used.
"""
from __future__ import annotations
import numpy as np
from scipy import ndimage
from local_l02_hue_conflict_abstain import _rgb_to_hsv_numpy
from local_l02_hue_extended_owner_shadow import (
    ExtendedOwnerHold, propose_hue_extended_owner_shadow,
    _assert_component_identity,
)

class NeutralUnderlayerHold(ValueError):
    pass

# Existing fixed hue-abstention neutral policy and contact-component floor.
NEUTRAL_SATURATION_MAX = 0.15
NEUTRAL_VALUE_MIN = 0.50
MIN_COMPONENT_PIXELS = 1024


def propose_neutral_underlayer_preservation_shadow(*, source_rgba: np.ndarray,
        class_ids: np.ndarray, frozen_owner: np.ndarray,
        composed_owner: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return (coat_owner, provisional_underlayer_mask, fail-closed receipt).

    This does not certify the provisional pixels as underlayer. Do not send
    the second array to the production renderer or substitute it for a Golden.
    When composed_owner is supplied, the original frozen owner is retained as
    provenance: rerunning hue on an already abstained composed owner loses the
    original underlayer source pixels.
    """
    shape = getattr(frozen_owner, 'shape', None)
    if (type(source_rgba) is not np.ndarray or source_rgba.dtype != np.uint8 or
        source_rgba.ndim != 3 or source_rgba.shape[-1] != 4 or
        type(frozen_owner) is not np.ndarray or frozen_owner.dtype != np.uint8 or
        frozen_owner.ndim != 2 or frozen_owner.size == 0 or
        type(class_ids) is not np.ndarray or class_ids.dtype != np.uint8 or
        class_ids.shape != shape or source_rgba.shape[:2] != shape):
        raise NeutralUnderlayerHold('INVALID_SOURCE_OR_MODEL_CONTRACT')
    if (np.any(class_ids >= 47) or np.any(frozen_owner > 2) or
        np.any((frozen_owner > 0) & (source_rgba[..., 3] == 0))):
        raise NeutralUnderlayerHold('INVALID_DOMAIN_OR_ALPHA')
    # This scoped hypothesis is only for a single frozen class10 coat owner.
    # H08's dual jacket/coat owner and any uncertain multi-owner case abstain.
    if (np.any(frozen_owner == 1) or
        np.count_nonzero((frozen_owner == 2) & (class_ids == 10)) < 64 or
        np.any((frozen_owner == 2) & ~np.isin(class_ids, (10, 32, 29, 30, 31)))):
        raise NeutralUnderlayerHold('NOT_SINGLE_COAT_OWNER_DOMAIN')
    if composed_owner is None:
        try:
            coat, _ = propose_hue_extended_owner_shadow(
                source_rgba=source_rgba, class_ids=class_ids, frozen_owner=frozen_owner)
        except ExtendedOwnerHold as exc:
            raise NeutralUnderlayerHold('HUE_TOPOLOGY_HOLD:' + str(exc)) from exc
        provenance_stage = 'hue_replay'
        input_promotions = 0
    else:
        if (type(composed_owner) is not np.ndarray or composed_owner.dtype != np.uint8 or
            composed_owner.shape != shape or np.any(composed_owner > 2) or
            np.any((composed_owner > 0) & (source_rgba[..., 3] == 0)) or
            np.any((frozen_owner > 0) & (composed_owner > 0) &
                   (frozen_owner != composed_owner)) or
            # Only class32 may be abstained by the pinned hue stage.
            # Component identity alone does not prevent catastrophic loss of
            # class10 coat core or preserved class29/30/31 extensions.
            np.any((frozen_owner > 0) & (composed_owner == 0) &
                   (class_ids != 32)) or
            np.any((composed_owner > 0) & (frozen_owner == 0) &
                   ~np.isin(class_ids, (30, 32))) or np.any(composed_owner == 1)):
            raise NeutralUnderlayerHold('INVALID_COMPOSED_OWNER_PROVENANCE')
        coat = composed_owner.copy()
        provenance_stage = 'composed_owner_provenance'
        input_promotions = int(np.count_nonzero((frozen_owner == 0) & (coat > 0)))
    _, saturation, value = _rgb_to_hsv_numpy(source_rgba[..., :3])
    neutral = ((frozen_owner == 2) & (coat == 0) & (class_ids == 32) &
               (source_rgba[..., 3] > 0) &
               (saturation < NEUTRAL_SATURATION_MAX) &
               (value > NEUTRAL_VALUE_MIN))
    # Preserve coherent source material, not scattered isolated edge pixels.
    components, n = ndimage.label(neutral, structure=np.ones((3, 3), dtype=bool))
    counts = np.bincount(components.ravel(), minlength=n + 1)
    keep = counts >= MIN_COMPONENT_PIXELS
    keep[0] = False
    candidate = neutral & keep[components]
    if (np.any(candidate & (coat > 0)) or
        np.any(candidate & (source_rgba[..., 3] == 0)) or
        np.any(candidate & ~((frozen_owner == 2) & (class_ids == 32))) or
        np.any((coat > 0) & (frozen_owner > 0) & (coat != frozen_owner))):
        raise NeutralUnderlayerHold('SOURCE_OR_EXCLUSIVE_OWNER_VIOLATION')
    try:
        for neighborhood in (4, 8):
            _assert_component_identity(frozen_owner, coat, 2, neighborhood)
    except ExtendedOwnerHold as exc:
        raise NeutralUnderlayerHold('COAT_COMPONENT_IDENTITY_HOLD') from exc
    return coat, candidate, {
        'schema': 'minimalizer/local-l02/neutral-underlayer-preservation-shadow/v1',
        'provenance_stage': provenance_stage,
        'composed_owner_input_promotions': input_promotions,
        'candidate_source_pixels': int(np.count_nonzero(candidate)),
        'candidate_components_8': int(np.count_nonzero(keep)),
        'coat_abstained_source_pixels': int(np.count_nonzero((frozen_owner == 2) & (coat == 0))),
        'frozen_owner_promotions': 0,
        'human_labels_used_for_inference': False,
        'unknown_pixels_not_treated_as_negative': True,
        'underlayer_semantic_owner_authorized': False,
        'known_case_exposed': True,
        'unseen_signed_blind': 'PENDING',
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
