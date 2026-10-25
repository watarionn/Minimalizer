"""Research-only sleeve cleanup BEFORE class30/32 contact opt-in.

The order matters: morphology cannot remove known-arm mistakes after they
become immutable owner pixels. Preserve all morphology-vetoed additions even
when the later opt-in proposes them again. No human masks/coordinates as input.
"""
from __future__ import annotations

import hashlib
import numpy as np
from scipy import ndimage
from local_l02_contact_density_palette_shadow import (
    ContactPaletteHold, propose_contact_density_palette_shadow,
)
from local_l02_contact_morphology_shadow import (
    ContactMorphologyHold, propose_contact_morphology_shadow,
)
from local_l02_hue_extended_owner_shadow import (
    ExtendedOwnerHold, _assert_component_identity,
)
from local_l02_cross_owner_contact_gate import (
    CrossOwnerContactHold, verify_no_new_cross_owner_contacts,
)


class MorphologyClass30Hold(ValueError):
    pass


def propose_morphology_then_class30_shadow(*, source_rgba: np.ndarray,
        class_ids: np.ndarray, anime_classes: np.ndarray,
        pre_palette_owner: np.ndarray,
        expected_pre_palette_sha256: str) -> tuple[np.ndarray, dict]:
    """Compose pinned pre-palette owner -> morphology -> class30/32 opt-in.

    A latest composed owner is NOT interchangeable with this earlier stage.
    """
    if (type(pre_palette_owner) is not np.ndarray or
            pre_palette_owner.dtype != np.uint8 or
            not isinstance(expected_pre_palette_sha256, str) or
            len(expected_pre_palette_sha256) != 64):
        raise MorphologyClass30Hold('INVALID_PRE_PALETTE_PIN')
    before_sha = hashlib.sha256(pre_palette_owner.tobytes()).hexdigest()
    if before_sha != expected_pre_palette_sha256:
        raise MorphologyClass30Hold('PRE_PALETTE_OWNER_SHA_MISMATCH')
    kwargs = dict(source_rgba=source_rgba, class_ids=class_ids,
                  anime_classes=anime_classes, baseline_owner=pre_palette_owner)
    try:
        raw_palette, _ = propose_contact_density_palette_shadow(**kwargs)
        cleaned, clean_meta = propose_contact_morphology_shadow(**kwargs)
        proposed, opt_meta = propose_contact_density_palette_shadow(
            source_rgba=source_rgba, class_ids=class_ids,
            anime_classes=anime_classes, baseline_owner=cleaned,
            eligible_classes=(30, 32))
    except (ContactPaletteHold, ContactMorphologyHold) as exc:
        raise MorphologyClass30Hold('SOURCE_STAGE_HOLD:' + str(exc)) from exc
    veto = ((pre_palette_owner == 0) & (raw_palette > 0) & (cleaned == 0))
    out = proposed.copy()
    resurrected = veto & (out > 0)
    out[veto] = 0
    st4 = ndimage.generate_binary_structure(2, 1)
    for owner in (1, 2):
        reachable = ndimage.binary_propagation(
            pre_palette_owner == owner, structure=st4, mask=out == owner)
        out[(pre_palette_owner == 0) & (out == owner) & ~reachable] = 0
    added = (pre_palette_owner == 0) & (out > 0)
    if (np.any((pre_palette_owner > 0) & (out != pre_palette_owner)) or
            np.any((out > 0) & (source_rgba[..., 3] == 0)) or
            np.any(added & ~np.isin(class_ids, (30, 32))) or
            np.any(veto & (out > 0))):
        raise MorphologyClass30Hold('FROZEN_SOURCE_OR_VETO_REGRESSION')
    try:
        for owner in (1, 2):
            for connectivity in (4, 8):
                _assert_component_identity(pre_palette_owner, out,
                                           owner, connectivity)
        verify_no_new_cross_owner_contacts(before=pre_palette_owner,
                                           after=out)
    except (ExtendedOwnerHold, CrossOwnerContactHold) as exc:
        raise MorphologyClass30Hold('COMPONENT_OR_CONTACT_HOLD') from exc
    return out, {
        'schema': 'minimalizer/local-l02/morphology-class30-composition/v0',
        'pre_palette_owner_sha256': before_sha,
        'morphology_owner_sha256': hashlib.sha256(cleaned.tobytes()).hexdigest(),
        'candidate_owner_sha256': hashlib.sha256(out.tobytes()).hexdigest(),
        'morphology_vetoed_px': int(np.count_nonzero(veto)),
        'optin_attempted_veto_resurrection_px': int(np.count_nonzero(resurrected)),
        'veto_resurrected_after_final_px': 0,
        'new_source_supported_px': int(np.count_nonzero(added)),
        'new_class30_px': int(np.count_nonzero(added & (class_ids == 30))),
        'new_class32_px': int(np.count_nonzero(added & (class_ids == 32))),
        'immutable_owner_changes_px': 0,
        'morphology_stage': clean_meta['schema'],
        'optin_stage': opt_meta['schema'],
        'human_labels_used_for_inference': False,
        'unknown_pixels_treated_as_negative': False,
        'known_case_exposed': True,
        'unseen_signed_blind': 'PENDING',
        'semantic_quality_pass': False,
        'Phase4': 'FAIL', 'L02': 'HOLD', 'L03': 'NO_GO',
        'Golden': 'HOLD', 'production': 'NO_GO',
    }
